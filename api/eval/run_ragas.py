#!/usr/bin/env python
"""
RAGAS evaluation script for the RAG pipeline.

Evaluates the RAG system using:
- Faithfulness: How grounded is the answer in the context?
- Answer Relevancy: How relevant is the answer to the question?
- Context Recall: How well does the retrieved context cover the answer?

Note: Requires 'ragas' package. Install with:
    pip install -r requirements-eval.txt
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import RAGAS (optional dependency)
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    )
    from langchain_openai import AzureChatOpenAI, ChatOpenAI
    from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False
    print("⚠️  RAGAS not installed. Install with: pip install -r requirements-eval.txt")
    print("Running basic evaluation without RAGAS metrics...\n")

from app.config import settings
from app.rag import RAGPipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_groundtruth(groundtruth_dir: str = None) -> List[Dict[str, Any]]:
    """
    Load ground truth questions and answers from JSONL files.
    
    Expected format:
    {
        "question": "Question text",
        "answer": "Expected answer",
        "metadata": {"product": "Auto", ...}
    }
    """
    groundtruth_dir = groundtruth_dir or settings.groundtruth_dir
    
    if not os.path.exists(groundtruth_dir):
        logger.error(f"Groundtruth directory not found: {groundtruth_dir}")
        return []
    
    qa_pairs = []
    
    # Load all .jsonl files
    for filepath in Path(groundtruth_dir).glob("*.jsonl"):
        logger.info(f"Loading groundtruth from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        qa_pairs.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse line: {e}")
    
    logger.info(f"Loaded {len(qa_pairs)} QA pairs")
    return qa_pairs


def run_rag_evaluation(rag_pipeline: RAGPipeline, qa_pairs: List[Dict[str, Any]]):
    """
    Run RAG pipeline on each question and collect results for RAGAS evaluation.
    
    Returns:
        Dataset with questions, ground_truth, answer, and contexts
    """
    questions = []
    ground_truths = []
    answers = []
    contexts_list = []
    
    for qa in qa_pairs:
        question = qa["question"]
        ground_truth = qa["answer"]
        filters = qa.get("metadata", {})
        
        logger.info(f"Processing: {question[:80]}...")
        
        try:
            # Run RAG pipeline
            result = rag_pipeline.retrieve_and_generate(
                query=question,
                filters=filters if filters else None
            )
            
            # Extract answer and contexts
            answer = result["answer"]
            citations = result["citations"]
            
            # Build contexts list from citations
            contexts = [cite["excerpt"] for cite in citations]
            
            questions.append(question)
            ground_truths.append(ground_truth)
            answers.append(answer)
            contexts_list.append(contexts)
            
            logger.info(f"✓ Generated answer ({len(answer)} chars, {len(contexts)} contexts)")
        
        except Exception as e:
            logger.error(f"Failed to process question: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Add placeholder to maintain alignment
            questions.append(question)
            ground_truths.append(ground_truth)
            answers.append("ERROR: Failed to generate answer")
            contexts_list.append([])
    
    # Return data for evaluation
    return {
        "questions": questions,
        "ground_truths": ground_truths,
        "answers": answers,
        "contexts": contexts_list,
    }


def create_ragas_dataset(eval_data: Dict[str, List]) -> 'Dataset':
    """Create RAGAS dataset from evaluation data."""
    if not RAGAS_AVAILABLE:
        return None
    
    dataset_dict = {
        "question": eval_data["questions"],
        "ground_truth": eval_data["ground_truths"],
        "answer": eval_data["answers"],
        "contexts": eval_data["contexts"],
    }
    
    return Dataset.from_dict(dataset_dict)


def get_ragas_llm_and_embeddings():
    """
    Get LLM and embeddings for RAGAS based on configuration.
    
    Returns:
        tuple: (llm, embeddings) for RAGAS evaluation
    """
    if not RAGAS_AVAILABLE:
        return None, None
    
    # Check if using Azure
    if settings.llm_provider == "azure":
        logger.info("Configuring RAGAS with Azure OpenAI")
        
        # Azure Chat LLM for RAGAS metrics
        llm = AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=settings.azure_openai_deployment,
            temperature=0,
        )
        
        # Azure Embeddings for RAGAS
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.openai_embedding_model,  # Use deployment name from config
        )
        
        logger.info(f"Using Azure deployment: {settings.azure_openai_deployment}")
    else:
        logger.info("Configuring RAGAS with OpenAI")
        
        # Standard OpenAI
        llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0,
        )
        
        embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )
    
    return llm, embeddings


def print_evaluation_report(results):
    """
    Print a formatted evaluation report.
    
    Args:
        results: EvaluationResult object from RAGAS
    """
    print("\n" + "="*60)
    print("RAGAS EVALUATION REPORT")
    print("="*60)
    
    # Convert EvaluationResult to pandas DataFrame
    try:
        df = results.to_pandas()
        
        # Calculate mean scores for each metric
        metric_scores = {}
        for col in df.columns:
            if col not in ['question', 'contexts', 'ground_truth', 'answer']:
                metric_scores[col] = df[col].mean()
        
        # Print metrics
        for metric, score in metric_scores.items():
            print(f"{metric:.<40} {score:.4f}")
        
        print("="*60)
        if metric_scores:
            avg_score = sum(metric_scores.values()) / len(metric_scores)
            print(f"Average Score: {avg_score:.4f}")
        print("="*60 + "\n")
        
        return metric_scores
        
    except Exception as e:
        logger.error(f"Failed to format results: {e}")
        print(f"Results: {results}")
        return {}


def main():
    """Main evaluation function."""
    logger.info("Starting RAGAS evaluation")
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    
    # Check if Qdrant has documents
    doc_count = rag_pipeline.vector_store.count_documents()
    logger.info(f"Qdrant collection '{settings.qdrant_collection}' has {doc_count} documents")
    
    if doc_count == 0:
        print("\n" + "="*70)
        print("⚠️  ERROR: Qdrant collection is EMPTY!")
        print("="*70)
        print(f"Collection name: {settings.qdrant_collection}")
        print(f"You need to ingest documents first!")
        print("\nTo ingest documents, run:")
        print("  1. Start the API: python -m uvicorn app.main:app --reload")
        print("  2. Call the ingest endpoint: POST http://localhost:8000/ingest")
        print("     Or use the web interface")
        print("="*70 + "\n")
        return
    
    # Load ground truth data
    logger.info("Loading ground truth data...")
    qa_pairs = load_groundtruth()
    
    if not qa_pairs:
        logger.error("No ground truth data found. Please add QA pairs to data/groundtruth/")
        return
    
    # Run evaluation
    logger.info(f"Running RAG evaluation on {len(qa_pairs)} questions...")
    eval_data = run_rag_evaluation(rag_pipeline, qa_pairs)
    
    # Check if we have valid data
    if not eval_data["questions"]:
        logger.error("No valid data for evaluation")
        return
    
    # Print basic results
    print("\n" + "="*70)
    print("RAG EVALUATION RESULTS")
    print("="*70)
    
    for i, (q, gt, a, c) in enumerate(zip(
        eval_data["questions"],
        eval_data["ground_truths"],
        eval_data["answers"],
        eval_data["contexts"]
    ), 1):
        print(f"\n{i}. QUESTION:")
        print(f"   {q}")
        print(f"\n   GROUND TRUTH:")
        print(f"   {gt[:150]}..." if len(gt) > 150 else f"   {gt}")
        print(f"\n   GENERATED ANSWER:")
        print(f"   {a[:200]}..." if len(a) > 200 else f"   {a}")
        print(f"\n   CONTEXTS RETRIEVED: {len(c)}")
        print("-" * 70)
    
    # Save basic results
    output_file = Path(settings.data_dir) / "evaluation_results_basic.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Basic results saved to {output_file}")
    
    # Try RAGAS evaluation if available
    if RAGAS_AVAILABLE:
        logger.info("\nCalculating RAGAS metrics...")
        try:
            dataset = create_ragas_dataset(eval_data)
            
            # Get LLM and embeddings (Azure or OpenAI)
            llm, embeddings = get_ragas_llm_and_embeddings()
            
            # Configure metrics with Azure/OpenAI LLM and embeddings
            metrics = [
                faithfulness,
                answer_relevancy,
                context_recall,
                context_precision,
            ]
            
            # Run RAGAS evaluation with custom LLM and embeddings
            logger.info(f"Running RAGAS with {settings.llm_provider.upper()} provider...")
            results = evaluate(
                dataset,
                metrics=metrics,
                llm=llm,
                embeddings=embeddings,
            )
            
            # Print RAGAS report
            print("\n" + "="*70)
            print("RAGAS METRICS")
            print("="*70)
            metric_scores = print_evaluation_report(results)
            
            # Save RAGAS results
            ragas_output = Path(settings.data_dir) / "evaluation_results_ragas.json"
            
            # Convert results to DataFrame and then to dict for JSON serialization
            try:
                df = results.to_pandas()
                results_dict = {
                    "summary": metric_scores,
                    "details": df.to_dict(orient='records')
                }
                
                with open(ragas_output, 'w', encoding='utf-8') as f:
                    json.dump(results_dict, f, indent=2, ensure_ascii=False)
                
                logger.info(f"RAGAS results saved to {ragas_output}")
            except Exception as e:
                logger.error(f"Failed to save RAGAS results: {e}")
        
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            if settings.llm_provider == "azure":
                logger.info("Note: RAGAS with Azure requires valid Azure OpenAI credentials")
                logger.info("Check AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, and AZURE_OPENAI_DEPLOYMENT")
            else:
                logger.info("Note: RAGAS requires OpenAI API key for evaluation metrics")
                logger.info("Set OPENAI_API_KEY in your environment or .env file")
    else:
        print("\n" + "="*70)
        print("⚠️  RAGAS metrics not available")
        print("="*70)
        print("To enable advanced metrics, install RAGAS:")
        print("  pip install -r requirements-eval.txt")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()



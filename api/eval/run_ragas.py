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


def print_evaluation_report(results: Dict[str, Any]):
    """Print a formatted evaluation report."""
    print("\n" + "="*60)
    print("RAGAS EVALUATION REPORT")
    print("="*60)
    
    for metric, score in results.items():
        if metric != "question" and metric != "contexts":
            print(f"{metric:.<40} {score:.4f}")
    
    print("="*60)
    print(f"Average Score: {sum(v for k, v in results.items() if k not in ['question', 'contexts']) / (len(results) - 2):.4f}")
    print("="*60 + "\n")


def main():
    """Main evaluation function."""
    logger.info("Starting RAGAS evaluation")
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    
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
            
            # Run RAGAS evaluation
            results = evaluate(
                dataset,
                metrics=[
                    faithfulness,
                    answer_relevancy,
                    context_recall,
                    context_precision,
                ],
            )
            
            # Print RAGAS report
            print("\n" + "="*70)
            print("RAGAS METRICS")
            print("="*70)
            print_evaluation_report(results)
            
            # Save RAGAS results
            ragas_output = Path(settings.data_dir) / "evaluation_results_ragas.json"
            with open(ragas_output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"RAGAS results saved to {ragas_output}")
        
        except Exception as e:
            logger.error(f"RAGAS evaluation failed: {e}")
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



import sys
import os
import pandas as pd
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_advisor import IntentDetector, BizMetricsContextBuilder, DeterministicFallback
from pipeline import run_pipeline, load_master_csv

def main():
    df = load_master_csv("c:/Users/Garv Ghanshani/Downloads/datasih/rural_business_master_data.csv")
    pipeline_result = run_pipeline(df)
    
    current_date = pd.to_datetime('2026-08-30')
    
    queries = [
        "How is my business performing?",
        "Why did my profit change?",
        "What products should I reorder?",
        "Which customers should I target?",
        "Who owes me money?",
        "Prepare my business for the next Indian festival.",
        "How can I improve sales?",
        "What are my biggest business risks?"
    ]
    
    for q in queries:
        intents = IntentDetector.detect(q)
        ctx = BizMetricsContextBuilder.build(pipeline_result, intents, current_date)
        fb = DeterministicFallback.generate(q, ctx, intents)
        
        print(f"\\n{'='*50}")
        print(f"QUERY: {q}")
        print(f"INTENTS: {intents}")
        print(f"CONTEXT KEYS INCLUDED: {list(ctx.keys())}")
        print(f"FALLBACK REC: {fb['recommendation']}")

if __name__ == "__main__":
    main()

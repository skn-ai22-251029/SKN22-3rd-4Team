import os
import sys
from pathlib import Path
import json
import pandas as pd
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from ragas.testset import TestsetGenerator
    from ragas.testset.synthesizers import (
        SingleHopSpecificQuerySynthesizer,
        MultiHopSpecificQuerySynthesizer,
        MultiHopAbstractQuerySynthesizer,
    )
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    # Load environment variables
    load_dotenv()
except ImportError as e:
    print(f"❌ ImportError: {e}")
    print(
        "💡 Please run 'pip install ragas pandas langchain_openai' to use this script."
    )
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)


def load_documents_with_context():
    """Load documents and enrich with company info, financials, and relationships."""
    print("⏳ CSV 파일 로딩 중...")

    # Paths
    project_root = Path(__file__).parent.parent.parent
    docs_path = project_root / "data" / "documents_rows.csv"
    companies_path = project_root / "data" / "companies_rows.csv"
    financials_path = project_root / "data" / "annual_reports_rows.csv"
    relationships_path = project_root / "data" / "company_relationships_rows.csv"

    if not docs_path.exists():
        print(f"❌ 문서를 찾을 수 없습니다: {docs_path}")
        return []

    # 1. Load DataFrames
    df_docs = pd.read_csv(docs_path)
    print(f"📄 문서 청크: {len(df_docs)}개")

    # Limit processing for cost control (as user requested to fit budget)
    # 100 chunks is a good representative sample
    sample_size = 100
    df_docs_sample = df_docs.sample(min(len(df_docs), sample_size), random_state=42)
    print(f"⚠️ 비용 최적화를 위해 {len(df_docs_sample)}개의 문서 청크를 샘플링합니다.")

    # 2. Build Lookups
    # Company Info
    ticker_to_info = {}
    if companies_path.exists():
        df_comp = pd.read_csv(companies_path)
        for _, row in df_comp.iterrows():
            ticker = row.get("ticker")
            if ticker:
                ticker_to_info[ticker] = {
                    "korean_name": row.get("korean_name", ticker),
                    "sector": row.get("sector", ""),
                    "industry": row.get("industry", ""),
                }

    # Financials (Latest year only for simplicity)
    company_id_to_ticker = {}  # Need to map UUIDs if annual_reports uses company_id
    # Assuming annual_reports links via company_id, we need to map that.
    # Looking at CSVs, companies_rows has 'id' and 'ticker'. annual_reports has 'company_id'.
    id_to_ticker = {}
    if companies_path.exists():
        df_comp = pd.read_csv(companies_path)
        id_to_ticker = dict(zip(df_comp["id"], df_comp["ticker"]))

    ticker_to_financials = {}
    if financials_path.exists():
        df_fin = pd.read_csv(financials_path)
        # Sort by fiscal_year desc to get latest
        df_fin = df_fin.sort_values("fiscal_year", ascending=False)
        for _, row in df_fin.iterrows():
            cid = row.get("company_id")
            ticker = id_to_ticker.get(cid)
            if ticker and ticker not in ticker_to_financials:  # Only store latest
                ticker_to_financials[ticker] = {
                    "revenue": row.get("revenue"),
                    "net_income": row.get("net_income"),
                    "year": row.get("fiscal_year"),
                }

    # Relationships
    ticker_to_relationships = {}
    if relationships_path.exists():
        df_rel = pd.read_csv(relationships_path)
        for _, row in df_rel.iterrows():
            src = row.get("source_ticker")
            target = row.get("target_company")  # Use name for readability
            rtype = row.get("relationship_type")

            if src:
                if src not in ticker_to_relationships:
                    ticker_to_relationships[src] = []
                if len(ticker_to_relationships[src]) < 5:  # Limit to top 5
                    ticker_to_relationships[src].append(f"{rtype}: {target}")

    # 3. Enrich Documents
    langchain_docs = []

    for _, row in df_docs_sample.iterrows():
        content = row["content"]
        try:
            metadata = (
                json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {}
            )
        except:
            metadata = {}

        ticker = metadata.get("ticker", "UNKNOWN")

        # Build Context String
        context_parts = []

        # Company Info
        info = ticker_to_info.get(ticker, {})
        k_name = info.get("korean_name", ticker)
        context_parts.append(f"Target Company: {k_name} ({ticker})")
        if info.get("sector"):
            context_parts.append(
                f"Sector: {info['sector']}, Industry: {info['industry']}"
            )

        # Financials
        fin = ticker_to_financials.get(ticker)
        if fin:
            context_parts.append(
                f"Financials ({fin['year']}): Revenue ${fin['revenue']}, Net Income ${fin['net_income']}"
            )

        # Relationships
        rels = ticker_to_relationships.get(ticker)
        if rels:
            context_parts.append("Relationships: " + ", ".join(rels))

        # Combine
        enrichment = "\n".join(context_parts) + "\n\n"
        full_content = enrichment + content

        # Add metadata
        metadata["korean_name"] = k_name

        doc = Document(page_content=full_content, metadata=metadata)
        langchain_docs.append(doc)

    return langchain_docs


def translate_to_korean(df, llm):
    """Translate Question and Ground Truth to Korean."""
    print("🇰🇷 생성된 질문과 답변을 한국어로 번역 중입니다...")

    # Translate to Korean
    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError:
        try:
            from langchain.prompts import ChatPromptTemplate
        except:
            print("❌ langchain.prompts import failed.")
            # Fallback or exit

    # Updated prompt to handle list/json formats if they appear
    translate_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant that translates English text to natural Korean for a financial Q&A dataset. Preserve technical terms if appropriate.",
            ),
            ("user", "Translate the following to Korean:\n\n{text}"),
        ]
    )

    chain = translate_prompt | llm

    translated_questions = []
    translated_grounds = []

    total = len(df)
    for i, row in df.iterrows():
        # Robust column access for different Ragas versions
        question = row.get("question") or row.get("user_input") or ""
        ground_truth = row.get("ground_truth") or row.get("reference") or ""

        if i % 10 == 0:
            print(f"[{i+1}/{total}] 번역 중...")

        try:
            # Check if empty
            if not question:
                translated_questions.append("")
            else:
                q_trans = chain.invoke({"text": question}).content
                translated_questions.append(q_trans)
        except Exception as e:
            print(f"Translation failed for Q {i}: {e}")
            translated_questions.append(question)

        try:
            if not ground_truth:
                translated_grounds.append("")
            else:
                g_trans = chain.invoke({"text": ground_truth}).content
                translated_grounds.append(g_trans)
        except Exception as e:
            print(f"Translation failed for GT {i}: {e}")
            translated_grounds.append(ground_truth)

    df["question_korean"] = translated_questions
    df["ground_truth_korean"] = translated_grounds

    # Determine target columns for original storage (handle case where 'question' might not be in index yet)
    q_col = (
        "question"
        if "question" in df.columns
        else ("user_input" if "user_input" in df.columns else "question")
    )
    gt_col = (
        "ground_truth"
        if "ground_truth" in df.columns
        else ("reference" if "reference" in df.columns else "ground_truth")
    )

    df["question_korean"] = translated_questions
    df["ground_truth_korean"] = translated_grounds

    # Store original for reference, use Korean as main
    df[f"{q_col}_original"] = df[q_col]
    df[f"{gt_col}_original"] = df[gt_col]

    # Always ensure 'question' and 'ground_truth' exist for evaluators
    df["question"] = df["question_korean"]
    df["ground_truth"] = df["ground_truth_korean"]

    return df


def generate_dataset():
    print("🚀 데이터셋 생성을 시작합니다 (Enhanced Context)...")

    documents = load_documents_with_context()
    if not documents:
        print("❌ 로드된 문서가 없습니다.")
        return

    # Generator 설정
    try:
        # User confirmed 'gpt-4.1-mini' is the correct model name for their environment.
        model_name = "gpt-4.1-mini"
        print(f"🤖 사용 모델: {model_name}")

        generator_llm = ChatOpenAI(model=model_name)
        critic_llm = ChatOpenAI(model=model_name)
        # User requested specific embedding model
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Ragas Wrapper
        generator_llm_wrapped = LangchainLLMWrapper(generator_llm)
        critic_llm_wrapped = LangchainLLMWrapper(critic_llm)
        embeddings_wrapped = LangchainEmbeddingsWrapper(embeddings)

        generator = TestsetGenerator(
            llm=generator_llm_wrapped, embedding_model=embeddings_wrapped
        )

        print("⏳ Ragas 데이터셋 생성 (영어)...")

        # Synthesizer 설정
        syn_simple = SingleHopSpecificQuerySynthesizer(llm=generator_llm_wrapped)
        syn_multi = MultiHopSpecificQuerySynthesizer(llm=generator_llm_wrapped)
        syn_abstract = MultiHopAbstractQuerySynthesizer(llm=generator_llm_wrapped)

        syn_simple.embeddings = embeddings_wrapped
        syn_multi.embeddings = embeddings_wrapped
        syn_abstract.embeddings = embeddings_wrapped

        # Generate English testset
        testset_size = 50

        testset = generator.generate_with_langchain_docs(
            documents,
            testset_size=testset_size,
            query_distribution=[
                (syn_simple, 0.5),
                (syn_multi, 0.3),
                (syn_abstract, 0.2),
            ],
        )

        # 저장 준비
        project_root = Path(__file__).parent.parent.parent
        output_dir = project_root / "data"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "evaluation_dataset.csv"

        df = testset.to_pandas()

        # Rename columns if Ragas used the new naming convention (user_input -> question, etc.)
        # This ensures the rest of the pipeline works smoothly.
        column_mapping = {
            "user_input": "question",
            "reference": "ground_truth",
            "reference_contexts": "contexts",
        }
        df = df.rename(
            columns={k: v for k, v in column_mapping.items() if k in df.columns}
        )

        # Save raw english first to be safe
        raw_output_path = output_dir / "evaluation_dataset_raw_english.csv"
        df.to_csv(raw_output_path, index=False)
        print(f"💾 영문 데이터셋 임시 저장 완료: {raw_output_path}")

        # Translate to Korean
        df = translate_to_korean(df, generator_llm)

        df.to_csv(output_path, index=False)
        print(f"✅ 데이터셋 생성 및 번역 완료: {output_path}")
        print(f"📊 생성된 데이터 개수: {len(df)}")
        print(df[["question", "ground_truth"]].head())

    except Exception as e:
        print(f"❌ 데이터셋 생성 중 오류 발생: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    generate_dataset()

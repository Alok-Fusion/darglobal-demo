"""
RAG Engine (Retrieval-Augmented Generation)
Implements high-accuracy hybrid retrieval combining lexical BM25 token matching,
field-specific weighting (Title, Brand, Location, Amenities), and metadata filtering.
"""

import json
import math
import os
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class RAGEngine:
    def __init__(self, knowledge_base_path: str):
        self.kb_path = knowledge_base_path
        self.documents: List[Dict[str, Any]] = []
        self.doc_tokens: List[List[str]] = []
        self.idf: Dict[str, float] = {}
        self.avg_doc_len: float = 0.0
        self.load_and_index()

    def tokenize(self, text: str) -> List[str]:
        """Simple, robust tokenization removing punctuation and converting to lowercase."""
        if not text:
            return []
        tokens = re.findall(r"\b[a-zA-Z0-9_\-\$€£]+\b", text.lower())
        return tokens

    def load_and_index(self):
        """Loads data from knowledge_base.json and computes BM25 statistics."""
        if not os.path.exists(self.kb_path):
            raise FileNotFoundError(f"Knowledge base file not found at: {self.kb_path}")

        with open(self.kb_path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

        total_tokens = 0
        doc_freqs: Counter = Counter()

        for doc in self.documents:
            # Combine weighted content
            text_repr = (
                (doc.get("title", "") + " ") * 4 +
                (doc.get("brand_partner", "") + " ") * 5 +
                (doc.get("city", "") + " " + doc.get("country", "") + " " + doc.get("district", "") + " ") * 3 +
                (doc.get("property_type", "") + " ") * 2 +
                doc.get("description", "") + " " +
                " ".join(doc.get("amenities", [])) + " " +
                doc.get("investment_highlights", "") + " " +
                doc.get("bedrooms", "") + " " + doc.get("status", "") + " " + doc.get("category", "") + " " +
                " ".join(f"{f.get('q', '')} {f.get('a', '')}" for f in doc.get("faqs", []) or []) + " " +
                doc.get("details", "")[:1500]
            )
            tokens = self.tokenize(text_repr)
            self.doc_tokens.append(tokens)
            total_tokens += len(tokens)

            unique_tokens = set(tokens)
            for token in unique_tokens:
                doc_freqs[token] += 1

        num_docs = len(self.documents)
        self.avg_doc_len = total_tokens / max(num_docs, 1)

        # Compute Robertson-Spärck Jones IDF
        for token, df in doc_freqs.items():
            self.idf[token] = math.log((num_docs - df + 0.5) / (df + 0.5) + 1.0)

    def search(
        self,
        query: str,
        top_k: int = 4,
        source_filter: str = "All",
        city_filter: str = "All",
        k1: float = 1.5,
        b: float = 0.75
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Retrieves top_k matching properties using BM25 scoring with exact phrase and keyword boosts.
        Supports dynamic source and city filtering.
        """
        query_tokens = self.tokenize(query)
        if not query_tokens:
            # If query is empty, return top records according to filters
            filtered = [
                d for d in self.documents
                if (source_filter == "All" or d.get("source") == source_filter)
                and (city_filter == "All" or city_filter.lower() in d.get("city", "").lower() or city_filter.lower() in d.get("district", "").lower())
            ]
            return [(d, 1.0) for d in filtered[:top_k]]

        scores: List[float] = []

        for idx, doc in enumerate(self.documents):
            # Apply source filter (DarGlobal / Wasalt / All)
            if source_filter != "All" and doc.get("source") != source_filter:
                scores.append(-999.0)
                continue

            # Apply city filter if set
            if city_filter != "All":
                city_text = (doc.get("city", "") + " " + doc.get("district", "")).lower()
                if city_filter.lower() not in city_text:
                    scores.append(-999.0)
                    continue

            doc_tokens = self.doc_tokens[idx]
            doc_len = len(doc_tokens)
            token_counts = Counter(doc_tokens)

            # BM25 baseline score
            bm25_score = 0.0
            for qt in query_tokens:
                if qt in token_counts:
                    tf = token_counts[qt]
                    idf = self.idf.get(qt, 0.1)
                    denom = tf + k1 * (1.0 - b + b * (doc_len / max(self.avg_doc_len, 1.0)))
                    bm25_score += idf * (tf * (k1 + 1.0)) / max(denom, 1e-6)

            # High-priority keyword and brand boosts
            query_lower = query.lower()
            bonus = 0.0

            title_lower = doc.get("title", "").lower()
            brand_lower = doc.get("brand_partner", "").lower()
            city_lower = doc.get("city", "").lower()
            district_lower = doc.get("district", "").lower()
            country_lower = doc.get("country", "").lower()

            for qt in query_tokens:
                if qt in brand_lower and qt not in ["the", "and", "by", "in", "of"]:
                    bonus += 8.0
                if qt in title_lower:
                    bonus += 5.0
                if qt in city_lower or qt in district_lower or qt in country_lower:
                    bonus += 4.0

            # Direct substring and location matches
            if brand_lower and brand_lower in query_lower and brand_lower != "n/a":
                bonus += 15.0
            if title_lower in query_lower:
                bonus += 20.0

            # Direct city, country, or source boost
            if city_lower and city_lower in query_lower:
                bonus += 16.0
            if country_lower and country_lower in query_lower:
                bonus += 12.0
            if district_lower and district_lower in query_lower:
                bonus += 16.0

            # Source priority matching
            if "wasalt" in query_lower and doc.get("source") == "Wasalt":
                bonus += 14.0
            if ("darglobal" in query_lower or "dar global" in query_lower) and doc.get("source") == "DarGlobal":
                bonus += 14.0

            total_score = bm25_score + bonus
            scores.append(total_score)

        # Rank and pick top_k
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.1:
                results.append((self.documents[idx], scores[idx]))

        # Fallback if no positive scores matched
        if not results:
            filtered = [
                d for d in self.documents
                if source_filter == "All" or d.get("source") == source_filter
            ]
            results = [(d, 0.5) for d in filtered[:top_k]]

        return results

    def build_system_context(self, retrieved_items: List[Tuple[Dict[str, Any], float]]) -> str:
        """Formats retrieved documents into a rich context block for LLM prompt injection."""
        if not retrieved_items:
            return "No specific property records retrieved."

        context_lines = []
        for i, (doc, score) in enumerate(retrieved_items, 1):
            amenities_str = ", ".join(doc.get("amenities", []))
            lines = [
                f"### [Property {i}] {doc.get('title')} ({doc.get('source')})",
                f"- **Brand Partner**: {doc.get('brand_partner', 'N/A')}",
                f"- **Location**: {doc.get('city')}, {doc.get('country')} ({doc.get('district')})",
                f"- **Property Type**: {doc.get('property_type')}",
                f"- **Bedrooms**: {doc.get('bedrooms')}",
                f"- **Price**: {doc.get('price_local')} ({doc.get('price_usd')})",
                f"- **Status / Handover**: {doc.get('status')}",
                f"- **Description**: {doc.get('description')}",
                f"- **Key Amenities**: {amenities_str}",
                f"- **Investment / Market Insights**: {doc.get('investment_highlights')}",
            ]
            if doc.get("area"):
                lines.append(f"- **Area**: {doc.get('area')}")
            faqs = doc.get("faqs") or []
            if faqs:
                lines.append("- **FAQ (from the page)**: " + " ".join(f"Q: {f['q']} A: {f['a']}" for f in faqs[:6])[:2500])
            if doc.get("details") and len(doc.get("description", "")) < 400:
                lines.append(f"- **More page text**: {doc['details'][:1200]}")
            lines.append(f"- **Official Link**: {doc.get('source_url')}")
            if doc.get("scraped_at"):
                lines.append(f"- **Scraped at**: {doc['scraped_at']}")
            context_lines.append("\n".join(lines))

        return "\n\n".join(context_lines)

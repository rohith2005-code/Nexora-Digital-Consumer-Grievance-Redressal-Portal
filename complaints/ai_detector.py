"""
AI Duplicate & Similar Complaint Detection Engine
Uses NLP text processing, tokenization, stopword removal, and fuzzy sequence matching
to detect duplicate or highly similar consumer grievances across the system.
"""

import re
import difflib
from collections import Counter


STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'itself', 'they', 'them', 'their',
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'because', 'as', 'until', 'while', 'of',
    'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    'can', 'will', 'just', 'should', 'now', 'is', 'was', 'are', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'the', 'received', 'got', 'product'
}


def tokenize_text(text):
    """Clean, lowercase and tokenize text into meaningful keywords."""
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS]


def calculate_jaccard_similarity(tokens1, tokens2):
    """Calculates Jaccard similarity coefficient between two token sets."""
    set1 = set(tokens1)
    set2 = set(tokens2)
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


def calculate_text_similarity(text1, text2):
    """
    Blends Jaccard token overlap and SequenceMatcher ratio
    for robust NLP text comparison.
    """
    tokens1 = tokenize_text(text1)
    tokens2 = tokenize_text(text2)

    jaccard = calculate_jaccard_similarity(tokens1, tokens2)
    seq_ratio = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    # Blended similarity score (60% token overlap + 40% sequence match)
    return (0.6 * jaccard) + (0.4 * seq_ratio)


def evaluate_complaint_similarity(complaint1, complaint2):
    """
    Evaluates similarity between two complaints across multiple dimensions:
    - Description text similarity (40% weight)
    - Product name similarity (30% weight)
    - Category match (15% weight)
    - Seller match (15% weight)
    """
    # 1. Description similarity
    desc_sim = calculate_text_similarity(complaint1.description, complaint2.description)

    # 2. Product name similarity
    prod_sim = calculate_text_similarity(complaint1.product_name, complaint2.product_name)

    # 3. Category match
    cat_match = 1.0 if complaint1.category == complaint2.category else 0.0

    # 4. Seller match
    seller_sim = difflib.SequenceMatcher(None, complaint1.seller.lower(), complaint2.seller.lower()).ratio()

    # Weighted aggregate score
    overall_score = (desc_sim * 0.40) + (prod_sim * 0.30) + (cat_match * 0.15) + (seller_sim * 0.15)

    # Extract common keywords for explanation
    tokens1 = set(tokenize_text(f"{complaint1.product_name} {complaint1.description}"))
    tokens2 = set(tokenize_text(f"{complaint2.product_name} {complaint2.description}"))
    matched_keywords = list(tokens1.intersection(tokens2))[:6]

    return {
        'score': round(overall_score * 100, 1),
        'matched_keywords': matched_keywords,
        'is_duplicate': overall_score >= 0.70,
        'is_similar': overall_score >= 0.50,
    }


def find_similar_complaints(target_complaint, all_complaints=None, threshold=50.0):
    """
    Compares target_complaint against database complaints and returns
    a sorted list of similar/duplicate candidates.
    """
    from .models import Complaint

    if all_complaints is None:
        all_complaints = Complaint.objects.exclude(id=target_complaint.id)

    results = []
    for other in all_complaints:
        sim_data = evaluate_complaint_similarity(target_complaint, other)
        if sim_data['score'] >= threshold:
            results.append({
                'complaint': other,
                'score': sim_data['score'],
                'is_duplicate': sim_data['is_duplicate'],
                'matched_keywords': sim_data['matched_keywords'],
            })

    # Sort highest similarity first
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]

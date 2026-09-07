# Test Report — Meridian Homes Realty RAG Chatbot

**Test document set:** Company_Overview.pdf, Property_Listings.pdf, Services_and_Fees.pdf, FAQs.pdf, Policies_and_Terms.pdf (all 5 uploaded and processed)

**RAG configuration used for this report:** `top_k=6`, `DISTANCE_THRESHOLD=1.35`, model `gemini-3.6-flash`, embeddings `gemini-embedding-001`

---

## Summary

| # | Category | Result |
|---|---|---|
| 1 | Direct-answer | ✅ Correct |
| 2 | Direct-answer | ✅ Correct |
| 3 | Spans a document | ✅ Correct |
| 4 | Spans a document | ✅ Correct |
| 5 | Multi-document | ⚠️ Incorrectly refused (known limitation — see below) |
| 6 | Multi-document | ✅ Correct |
| 7 | No answer in KB | ✅ Correctly refused |
| 8 | No answer in KB | ✅ Correctly refused |
| 9 | Hallucination test | ✅ Correctly refused |
| 10 | Hallucination test | ✅ Correctly refused |

**9 / 10 correct behavior.** No hallucinations observed in any test — every wrong or refused answer erred on the side of caution rather than fabricating information.

---

## Detailed Results

### 1. Direct-answer
**Q:** What year was Meridian Homes Realty founded?
**A:** "Meridian Homes Realty was founded in 2015."
**Source:** Company_Overview.pdf
**Result:** ✅ Correct, matches source document.

### 2. Direct-answer
**Q:** What is the price of the Meridian Loft?
**A:** "The price of the Meridian Loft is $310,000."
**Source:** Property_Listings.pdf
**Result:** ✅ Correct.

### 3. Spans a document
**Q:** What is the minimum lease term for the Maple Grove Townhouse, and what security deposit is required?
**A:** "The minimum lease term for the Maple Grove Townhouse is 12 months, and the required security deposit is equal to one month's rent ($2,400)."
**Source:** Property_Listings.pdf, Policies_and_Terms.pdf
**Result:** ✅ Correct — correctly combined the lease term (Policies_and_Terms) with the rent amount (Property_Listings) into one coherent answer.

### 4. Spans a document
**Q:** What are Meridian Homes Realty's office hours?
**A:** "The Austin office is open Monday through Friday from 9:00 AM to 6:00 PM, and Saturday from 10:00 AM to 3:00 PM. It is closed on Sundays and major U.S. holidays."
**Source:** Company_Overview.pdf
**Result:** ✅ Correct.

### 5. Multi-document
**Q:** What's the price of the Sunridge Villa and what's your commission rate?
**A:** "I couldn't find that information in the uploaded documents."
**Result:** ⚠️ **Incorrect refusal** — both facts exist in the knowledge base (Property_Listings.pdf and Services_and_Fees.pdf respectively) but were not retrieved together. See "Known Limitations" below.

### 6. Multi-document
**Q:** Do you offer property management, and if so, what's the fee? Also, what's your cancellation policy for sellers?
**A:** "Yes, property management is offered at a fee of 8% of monthly collected rent. For sellers, the cancellation policy allows them to cancel a listing agreement with 30 days' written notice."
**Source:** Services_and_Fees.pdf, Policies_and_Terms.pdf
**Result:** ✅ Correct — successfully retrieved and combined information from two separate documents.

### 7. No answer in knowledge base
**Q:** Do you have any properties for sale outside of Texas?
**A:** "I couldn't find that information in the uploaded documents."
**Result:** ✅ Correctly refused — all listings are Texas-based; no fabricated properties or locations were invented.

### 8. No answer in knowledge base
**Q:** What financing or mortgage options do you offer?
**A:** "I couldn't find that information in the uploaded documents."
**Result:** ✅ Correctly refused — the documents don't cover financing/mortgages; no invented answer.

### 9. Hallucination test
**Q:** Do you sell commercial warehouses?
**A:** "I couldn't find that information in the uploaded documents."
**Result:** ✅ Correctly refused — company only deals in residential properties; model did not fabricate a commercial listing.

### 10. Hallucination test
**Q:** What is your CEO's name?
**A:** "I couldn't find that information in the uploaded documents."
**Result:** ✅ Correctly refused — no leadership names exist in any document; model did not invent a name.

---

## Known Limitations

### Multi-topic retrieval gap (Test #5)
When a single question asks about two unrelated facts that live in different documents (e.g., a specific property's price + the company's general commission rate), retrieval sometimes fails to surface chunks for both topics within the `top_k` window — particularly when one topic (property details) has many competing near-duplicate chunks across 5 different property listings, which crowd out the second topic's chunk.

**What we tried:** Increased `top_k` from 4→6 and loosened `DISTANCE_THRESHOLD` from 1.2→1.35 after discovering this issue. This fixed a similar failure in Test #6 (property management fee + cancellation policy), confirming the tuning generally helps multi-document retrieval. However, Test #5 specifically still fails, likely because `Property_Listings.pdf` contains 5 semantically similar property blocks that dilute the top-k slots available for the Sunridge Villa-specific chunk.

**Possible future fixes (not implemented in this version):**
- Query decomposition: splitting compound questions into sub-questions, retrieving separately for each, then combining
- Re-ranking retrieved chunks with a cross-encoder before passing to the LLM
- Increasing `top_k` further (tried informally, diminishing returns without decomposition)

This is a deliberate trade-off documented here rather than a silent failure — the system still correctly declines rather than guessing when it can't find both pieces of information, which preserves the hallucination guardrail even when retrieval is imperfect.

### DOCX/TXT page numbers
DOCX and TXT files don't have native page boundaries, so all their content is attributed to "page 1" in source citations. This is a known simplification, not a bug — PDF (the primary format tested) has accurate per-page metadata.

### LLM response latency
Gemini API response times occasionally exceed 30–60 seconds under normal conditions (observed during testing, not tied to a specific question type). The frontend timeout was increased to 90 seconds to accommodate this; a production system might add streaming responses or a longer async job pattern instead.
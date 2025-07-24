# email_classifier/ml/classifier.py

from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

class PublicModelEmailClassifier:
    def __init__(self):
        """Initialize with pre-trained public models - no training needed!"""
        
        # Option 1: Use a general-purpose email classification model
        try:
            # This model is trained on email/customer service data
            self.email_model = pipeline(
                "text-classification",
                model="unitary/toxic-bert",  # Good for filtering
                device=0 if torch.cuda.is_available() else -1
            )
        except:
            self.email_model = None
        
        # Option 2: Best zero-shot classification model (Facebook's)
        self.zero_shot_classifier = pipeline(
            "zero-shot-classification", 
            model="facebook/bart-large-mnli",  # Public Facebook model
            device=0 if torch.cuda.is_available() else -1
        )
        
        # Option 3: Sentence similarity model for semantic matching
        try:
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')  # Public model
            self.use_sentence_transformer = True
        except ImportError:
            print("sentence-transformers not installed. Using transformers only.")
            self.use_sentence_transformer = False
        
        # Department labels and their semantic descriptions
        self.departments = ["HR", "Accounting", "Support", "B2B"]
        
        # Enhanced descriptions for better classification
        self.dept_descriptions = {
            "HR": "human resources employee benefits payroll hiring staff recruitment performance review personal information employee handbook vacation sick leave",
            "Accounting": "invoice billing payment financial accounting budget expenses receipt tax money cost pricing financial report accounts payable receivable",
            "Support": "technical support help troubleshooting problem issue bug error password computer software system access login maintenance repair",
            "B2B": "business partnership enterprise corporate sales meeting collaboration bulk pricing company organization contract proposal deal negotiation"
        }
        
        # Keyword matching for backup classification
        self.keywords = {
            "HR": ["hr", "human resources", "employee", "payroll", "benefits", "hiring", "recruitment", "staff", "vacation", "sick leave", "performance", "handbook", "personal"],
            "Accounting": ["invoice", "bill", "payment", "finance", "accounting", "budget", "expense", "receipt", "tax", "money", "cost", "price", "financial", "accounts"],
            "Support": ["help", "support", "problem", "issue", "bug", "error", "password", "computer", "software", "system", "access", "login", "technical", "repair", "maintenance"],
            "B2B": ["partnership", "enterprise", "corporate", "business", "bulk", "collaboration", "meeting", "company", "organization", "contract", "proposal", "deal", "sales"]
        }
    
    def classify_email_zero_shot(self, text: str) -> tuple:
        """Use Facebook's BART model for zero-shot classification"""
        # Method 1: Use simple labels
        result1 = self.zero_shot_classifier(text, self.departments)
        
        # Method 2: Use descriptive labels for better accuracy
        descriptions = list(self.dept_descriptions.values())
        result2 = self.zero_shot_classifier(text, descriptions)
        
        # Map description back to department
        best_desc = result2["labels"][0]
        best_dept = None
        for dept, desc in self.dept_descriptions.items():
            if desc == best_desc:
                best_dept = dept
                break
        
        # Combine both methods (weighted average)
        if best_dept and best_dept == result1["labels"][0]:
            # Both methods agree - high confidence
            confidence = (result1["scores"][0] + result2["scores"][0]) / 2
            return best_dept, confidence
        else:
            # Use the higher confidence one
            if result1["scores"][0] > result2["scores"][0]:
                return result1["labels"][0], result1["scores"][0]
            else:
                return best_dept or result1["labels"][0], result2["scores"][0]
    
    def classify_email_similarity(self, text: str) -> tuple:
        """Use sentence transformers for semantic similarity"""
        if not self.use_sentence_transformer:
            return self.classify_email_zero_shot(text)
        
        # Encode the input text
        text_embedding = self.sentence_model.encode(text)
        
        # Calculate similarity with each department description
        similarities = {}
        for dept, desc in self.dept_descriptions.items():
            dept_embedding = self.sentence_model.encode(desc)
            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(text_embedding).unsqueeze(0),
                torch.tensor(dept_embedding).unsqueeze(0)
            ).item()
            similarities[dept] = similarity
        
        # Get the best match
        best_dept = max(similarities, key=similarities.get)
        confidence = similarities[best_dept]
        
        return best_dept, confidence
    
    def classify_email_keywords(self, text: str) -> tuple:
        """Keyword-based classification as backup"""
        text_lower = text.lower()
        scores = {}
        
        for dept, words in self.keywords.items():
            score = sum(1 for word in words if word in text_lower)
            # Normalize by text length to avoid bias toward longer texts
            normalized_score = score / max(len(text_lower.split()), 1)
            scores[dept] = normalized_score
        
        if not scores or max(scores.values()) == 0:
            return "Support", 0.1  # Default fallback
        
        best_dept = max(scores, key=scores.get)
        confidence = scores[best_dept]
        
        return best_dept, min(confidence, 1.0)  # Cap at 1.0
    
    def classify_email(self, text: str) -> str:
        """
        Main classification method using ensemble of public models
        
        Args:
            text: Email content to classify
            
        Returns:
            str: Department name (HR, Accounting, Support, B2B)
        """
        if not text or len(text.strip()) < 3:
            return "Support"  # Default for very short texts
        
        # Get predictions from multiple methods
        zero_shot_dept, zero_shot_conf = self.classify_email_zero_shot(text)
        
        if self.use_sentence_transformer:
            similarity_dept, similarity_conf = self.classify_email_similarity(text)
        else:
            similarity_dept, similarity_conf = zero_shot_dept, zero_shot_conf
        
        keyword_dept, keyword_conf = self.classify_email_keywords(text)
        
        # Ensemble voting with confidence weighting
        votes = {}
        
        # Zero-shot gets highest weight (most accurate)
        votes[zero_shot_dept] = votes.get(zero_shot_dept, 0) + zero_shot_conf * 0.6
        
        # Similarity gets medium weight
        votes[similarity_dept] = votes.get(similarity_dept, 0) + similarity_conf * 0.3
        
        # Keywords get lowest weight (backup)
        votes[keyword_dept] = votes.get(keyword_dept, 0) + keyword_conf * 0.1
        
        # Return the department with highest weighted vote
        best_dept = max(votes, key=votes.get)
        return best_dept
    
    def classify_with_confidence(self, text: str) -> tuple:
        """
        Classify email and return confidence score
        
        Args:
            text: Email content to classify
            
        Returns:
            tuple: (department_name, confidence_score)
        """
        if not text or len(text.strip()) < 3:
            return "Support", 0.1
        
        # Get the main prediction
        dept = self.classify_email(text)
        
        # Get confidence from zero-shot (most reliable)
        _, confidence = self.classify_email_zero_shot(text)
        
        return dept, confidence
    
    def classify_batch(self, texts: list) -> list:
        """
        Classify multiple emails efficiently
        
        Args:
            texts: List of email texts
            
        Returns:
            list: List of department names
        """
        return [self.classify_email(text) for text in texts]

# Global instance for performance (loads models once)
_classifier = None

def get_classifier():
    """Get or create the classifier instance"""
    global _classifier
    if _classifier is None:
        print("🚀 Loading public models (first time only)...")
        print("📦 Using Facebook BART-large-mnli (public model)")
        _classifier = PublicModelEmailClassifier()
        print("✅ Models loaded! Ready to classify emails.")
    return _classifier

# Simple functions for easy use
def classify_email(text: str) -> str:
    """
    Classify an email using public pre-trained models
    
    Args:
        text: Email content
        
    Returns:
        str: Department (HR, Accounting, Support, B2B)
    """
    classifier = get_classifier()
    return classifier.classify_email(text)

def classify_email_with_score(text: str) -> tuple:
    """
    Classify email with confidence score
    
    Args:
        text: Email content
        
    Returns:
        tuple: (department, confidence_score)
    """
    classifier = get_classifier()
    return classifier.classify_with_confidence(text)

def classify_multiple_emails(emails: list) -> list:
    """
    Classify multiple emails at once
    
    Args:
        emails: List of email texts
        
    Returns:
        list: List of departments
    """
    classifier = get_classifier()
    return classifier.classify_batch(emails)

# Test the classifier with public models
if __name__ == "__main__":
    # Test emails
    test_emails = [
        "Can you please resend the invoice for April?",
        "I need help with my password reset",
        "When is the next employee meeting scheduled?",
        "We would like to discuss enterprise pricing options",
        "My laptop won't connect to the office wifi",
        "I need to update my tax withholding information",
        "Can we schedule a call about partnership opportunities?",
        "The application keeps crashing when I try to login",
        "Please send me my pay stub for last month",
        "I'm interested in bulk licensing for our company"
    ]
    
    print("🎯 Testing Public Model Email Classifier")
    print("📊 Using Facebook BART-large-mnli + Ensemble Methods")
    print("=" * 70)
    
    # Individual classification with confidence
    for i, email in enumerate(test_emails, 1):
        dept = classify_email(email)
        dept_with_score, confidence = classify_email_with_score(email)
        
        print(f"📧 Email {i}: '{email[:45]}...'")
        print(f"🎯 Department: {dept}")
        print(f"📈 Confidence: {confidence:.1%}")
        print("-" * 70)
    
    # Batch classification demo
    print("\n⚡ Batch Classification Results:")
    departments = classify_multiple_emails(test_emails)
    for i, (email, dept) in enumerate(zip(test_emails, departments), 1):
        print(f"{i:2d}. {dept:10} | {email[:40]}...")
    
    print(f"\n✨ Classification complete using public models!")
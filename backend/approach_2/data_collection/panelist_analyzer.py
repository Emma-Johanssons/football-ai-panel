"""
Analyzer for football panel show participants' speaking patterns and characteristics
"""
import os
import json
from typing import Dict, List, Optional
import speech_recognition as sr
from pydub import AudioSegment
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter

class PanelistAnalyzer:
    def __init__(self):
        # Download required NLTK data
        nltk.download('punkt')
        nltk.download('vader_lexicon')
        
        self.recognizer = sr.Recognizer()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Initialize pattern trackers
        self.speaking_patterns = {
            "catchphrases": Counter(),
            "transitions": Counter(),
            "interruptions": Counter(),
            "agreements": Counter(),
            "disagreements": Counter()
        }
        
        # Common football phrases to track
        self.football_phrases = {
            "tactical": ["formation", "press", "system", "setup", "structure"],
            "statistical": ["possession", "shots", "passes", "expected goals", "stats"],
            "emotional": ["brilliant", "fantastic", "poor", "terrible", "incredible"],
            "analytical": ["if you look at", "what's interesting is", "the key here is"]
        }
        
    def analyze_audio_file(self, audio_file: str, panelist_id: str) -> Dict:
        """Analyze an audio file for a specific panelist"""
        try:
            # Load audio file
            audio = AudioSegment.from_mp3(audio_file)
            
            # Convert to wav for speech recognition
            wav_path = audio_file.replace(".mp3", ".wav")
            audio.export(wav_path, format="wav")
            
            # Perform speech recognition
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                
            # Analyze the text
            analysis = self._analyze_text(text, panelist_id)
            
            # Clean up temporary file
            os.remove(wav_path)
            
            return analysis
            
        except Exception as e:
            print(f"Error analyzing audio file: {e}")
            return {}
            
    def _analyze_text(self, text: str, panelist_id: str) -> Dict:
        """Analyze transcribed text for patterns and characteristics"""
        sentences = sent_tokenize(text)
        words = word_tokenize(text.lower())
        
        analysis = {
            "panelist_id": panelist_id,
            "speaking_patterns": {},
            "vocabulary": set(),
            "sentiment_analysis": {},
            "topic_focus": {},
            "interaction_style": {}
        }
        
        # Analyze vocabulary and phrases
        analysis["vocabulary"] = set(words)
        analysis["speaking_patterns"] = self._analyze_speaking_patterns(sentences)
        
        # Analyze sentiment
        sentiment_scores = [
            self.sentiment_analyzer.polarity_scores(sentence)
            for sentence in sentences
        ]
        analysis["sentiment_analysis"] = {
            "average_sentiment": sum(s["compound"] for s in sentiment_scores) / len(sentiment_scores),
            "sentiment_distribution": {
                "positive": len([s for s in sentiment_scores if s["compound"] > 0.2]),
                "neutral": len([s for s in sentiment_scores if -0.2 <= s["compound"] <= 0.2]),
                "negative": len([s for s in sentiment_scores if s["compound"] < -0.2])
            }
        }
        
        # Analyze topic focus
        analysis["topic_focus"] = self._analyze_topic_focus(text)
        
        # Analyze interaction style
        analysis["interaction_style"] = self._analyze_interaction_style(sentences)
        
        return analysis
        
    def _analyze_speaking_patterns(self, sentences: List[str]) -> Dict:
        """Analyze speaking patterns and common phrases"""
        patterns = {
            "sentence_length": sum(len(word_tokenize(s)) for s in sentences) / len(sentences),
            "catchphrases": self._find_catchphrases(sentences),
            "transitions": self._find_transitions(sentences),
            "emphasis_patterns": self._find_emphasis_patterns(sentences)
        }
        return patterns
        
    def _find_catchphrases(self, sentences: List[str]) -> List[str]:
        """Find commonly repeated phrases"""
        phrases = []
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            for i in range(len(words)-2):
                phrase = " ".join(words[i:i+3])
                self.speaking_patterns["catchphrases"][phrase] += 1
                
        # Return most common phrases
        return [phrase for phrase, count in self.speaking_patterns["catchphrases"].most_common(5)]
        
    def _find_transitions(self, sentences: List[str]) -> List[str]:
        """Find transition phrases used"""
        transition_words = ["however", "moreover", "furthermore", "looking at", "if we consider"]
        transitions = []
        
        for sentence in sentences:
            words = word_tokenize(sentence.lower())
            for trans in transition_words:
                if trans in words:
                    transitions.append(trans)
                    self.speaking_patterns["transitions"][trans] += 1
                    
        return transitions
        
    def _find_emphasis_patterns(self, sentences: List[str]) -> Dict:
        """Find patterns of emphasis and expression"""
        emphasis = {
            "repetition": 0,
            "strong_statements": 0,
            "questions": 0
        }
        
        for sentence in sentences:
            # Check for repetition
            words = word_tokenize(sentence.lower())
            if len(set(words)) < len(words) * 0.8:  # 20% repetition threshold
                emphasis["repetition"] += 1
                
            # Check for strong statements
            if any(word in sentence.lower() for word in ["definitely", "absolutely", "certainly"]):
                emphasis["strong_statements"] += 1
                
            # Check for questions
            if "?" in sentence or sentence.lower().startswith(("what", "why", "how", "when")):
                emphasis["questions"] += 1
                
        return emphasis
        
    def _analyze_topic_focus(self, text: str) -> Dict:
        """Analyze what football aspects the panelist focuses on"""
        focus = {category: 0 for category in self.football_phrases}
        
        for category, phrases in self.football_phrases.items():
            for phrase in phrases:
                focus[category] += text.lower().count(phrase)
                
        # Convert to percentages
        total = sum(focus.values()) or 1  # Avoid division by zero
        return {k: (v/total)*100 for k, v in focus.items()}
        
    def _analyze_interaction_style(self, sentences: List[str]) -> Dict:
        """Analyze how the panelist interacts with others"""
        style = {
            "agreeable": 0,
            "confrontational": 0,
            "analytical": 0,
            "passionate": 0
        }
        
        agreement_phrases = ["agree", "good point", "exactly", "right"]
        disagreement_phrases = ["disagree", "no way", "wrong", "not true"]
        analytical_phrases = ["if you look at", "statistically", "analysis shows"]
        passion_phrases = ["love", "hate", "amazing", "terrible"]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check agreement level
            if any(phrase in sentence_lower for phrase in agreement_phrases):
                style["agreeable"] += 1
                
            if any(phrase in sentence_lower for phrase in disagreement_phrases):
                style["confrontational"] += 1
                
            if any(phrase in sentence_lower for phrase in analytical_phrases):
                style["analytical"] += 1
                
            if any(phrase in sentence_lower for phrase in passion_phrases):
                style["passionate"] += 1
                
        return style
        
    def aggregate_analysis(self, panelist_name: str) -> Dict:
        """Aggregate analysis results for a panelist across multiple shows"""
        # Load all analysis files for this panelist
        analyses = []
        analysis_dir = "data/processed_data"
        
        for filename in os.listdir(analysis_dir):
            if panelist_name.lower().replace(" ", "_") in filename:
                with open(os.path.join(analysis_dir, filename), 'r') as f:
                    analyses.append(json.load(f))
                    
        if not analyses:
            return None
            
        # Aggregate the data
        aggregated = {
            "panelist_name": panelist_name,
            "speaking_patterns": self._aggregate_speaking_patterns(analyses),
            "topic_focus": self._aggregate_topic_focus(analyses),
            "interaction_style": self._aggregate_interaction_style(analyses),
            "vocabulary": self._aggregate_vocabulary(analyses),
            "overall_sentiment": self._aggregate_sentiment(analyses)
        }
        
        return aggregated
        
    def _aggregate_speaking_patterns(self, analyses: List[Dict]) -> Dict:
        """Aggregate speaking patterns across analyses"""
        patterns = {
            "common_phrases": Counter(),
            "avg_sentence_length": 0,
            "transition_usage": Counter(),
            "emphasis_patterns": {
                "repetition": 0,
                "strong_statements": 0,
                "questions": 0
            }
        }
        
        for analysis in analyses:
            if "speaking_patterns" in analysis:
                sp = analysis["speaking_patterns"]
                patterns["avg_sentence_length"] += sp.get("sentence_length", 0)
                patterns["common_phrases"].update(sp.get("catchphrases", []))
                patterns["transition_usage"].update(sp.get("transitions", []))
                
                if "emphasis_patterns" in sp:
                    for key in patterns["emphasis_patterns"]:
                        patterns["emphasis_patterns"][key] += sp["emphasis_patterns"].get(key, 0)
                        
        # Average out the values
        if analyses:
            patterns["avg_sentence_length"] /= len(analyses)
            for key in patterns["emphasis_patterns"]:
                patterns["emphasis_patterns"][key] /= len(analyses)
                
        return patterns
        
    def _aggregate_topic_focus(self, analyses: List[Dict]) -> Dict:
        """Aggregate topic focus across analyses"""
        focus = {category: 0 for category in self.football_phrases}
        
        for analysis in analyses:
            if "topic_focus" in analysis:
                for category in focus:
                    focus[category] += analysis["topic_focus"].get(category, 0)
                    
        # Average the percentages
        if analyses:
            focus = {k: v/len(analyses) for k, v in focus.items()}
            
        return focus
        
    def _aggregate_interaction_style(self, analyses: List[Dict]) -> Dict:
        """Aggregate interaction style across analyses"""
        style = {
            "agreeable": 0,
            "confrontational": 0,
            "analytical": 0,
            "passionate": 0
        }
        
        for analysis in analyses:
            if "interaction_style" in analysis:
                for key in style:
                    style[key] += analysis["interaction_style"].get(key, 0)
                    
        # Average the values
        if analyses:
            style = {k: v/len(analyses) for k, v in style.items()}
            
        return style
        
    def _aggregate_vocabulary(self, analyses: List[Dict]) -> Dict:
        """Aggregate vocabulary statistics across analyses"""
        all_words = set()
        for analysis in analyses:
            if "vocabulary" in analysis:
                all_words.update(analysis["vocabulary"])
                
        return {
            "unique_words": len(all_words),
            "common_words": list(Counter(word for analysis in analyses 
                                      for word in analysis.get("vocabulary", [])).most_common(20))
        }
        
    def _aggregate_sentiment(self, analyses: List[Dict]) -> Dict:
        """Aggregate sentiment analysis across analyses"""
        sentiment = {
            "average": 0,
            "distribution": {
                "positive": 0,
                "neutral": 0,
                "negative": 0
            }
        }
        
        for analysis in analyses:
            if "sentiment_analysis" in analysis:
                sa = analysis["sentiment_analysis"]
                sentiment["average"] += sa.get("average_sentiment", 0)
                for key in sentiment["distribution"]:
                    sentiment["distribution"][key] += sa.get("sentiment_distribution", {}).get(key, 0)
                    
        # Average the values
        if analyses:
            sentiment["average"] /= len(analyses)
            sentiment["distribution"] = {k: v/len(analyses) for k, v in sentiment["distribution"].items()}
            
        return sentiment 
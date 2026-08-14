/**
 * AI Interview Practice Data Types.
 */

export interface QuestionFeedback {
  questionId: string;
  questionText: string;
  userAnswer: string;
  technicalScore: number;
  communicationScore: number;
  keyStrengths: string[];
  suggestedImprovements: string[];
}

export interface AIInterviewSession {
  id: string;
  targetRole: string;
  date: string;
  overallScore: number;
  feedbacks: QuestionFeedback[];
}

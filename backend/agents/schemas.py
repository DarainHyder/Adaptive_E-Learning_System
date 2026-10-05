"""Pydantic schemas used for LLM structured outputs (LangChain `with_structured_output`)."""
from typing import List, Literal

from pydantic import BaseModel, Field

Difficulty = Literal['beginner', 'intermediate', 'advanced']


class LessonSection(BaseModel):
    title: str = Field(description='Section heading')
    body_markdown: str = Field(description='Section content in Markdown. Use ```python fences for code.')


class CodeExample(BaseModel):
    title: str
    code: str = Field(description='Runnable code, no Markdown fences')
    language: str = Field(default='python')
    explanation: str


class PracticeChallenge(BaseModel):
    prompt: str = Field(description='A single, self-contained exercise')
    starter_code: str = Field(description='Starter code with TODOs; must run in plain Python with no imports beyond the standard library')
    expected_output: str
    hints: List[str] = Field(description='Three progressively more revealing hints')


class Lesson(BaseModel):
    title: str
    summary: str = Field(description='Two-sentence overview')
    objectives: List[str] = Field(description='3-4 measurable learning objectives')
    sections: List[LessonSection]
    code_examples: List[CodeExample]
    key_takeaways: List[str]
    practice: PracticeChallenge
    estimated_minutes: int = Field(ge=3, le=60)


class QuizOptions(BaseModel):
    A: str
    B: str
    C: str
    D: str


class QuizQuestion(BaseModel):
    question: str
    options: QuizOptions
    correct_answer: Literal['A', 'B', 'C', 'D']
    explanation: str = Field(description='Why the answer is correct and why the main distractor is wrong (2-3 sentences)')
    difficulty: Difficulty
    concept: str = Field(description='The key concept this question assesses')


class Quiz(BaseModel):
    questions: List[QuizQuestion]


class Hint(BaseModel):
    hint: str = Field(description='The hint (2-4 sentences, no full solution unless the level is detailed)')
    guiding_question: str = Field(default='', description='Optional question that nudges the learner')

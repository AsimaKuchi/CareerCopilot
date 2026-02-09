import React, { useState, useEffect } from "react";
import { API } from "@/App";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  HelpCircle,
  Plus,
  Save,
  Loader2,
  CheckCircle,
  ClipboardList,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";

export default function ScreeningQuestions() {
  const [templates, setTemplates] = useState([]);
  const [answers, setAnswers] = useState({});
  const [customQuestions, setCustomQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showAddCustom, setShowAddCustom] = useState(false);
  const [newQuestion, setNewQuestion] = useState("");
  const [newAnswer, setNewAnswer] = useState("");

  useEffect(() => {
    fetchScreeningData();
  }, []);

  const fetchScreeningData = async () => {
    try {
      const response = await fetch(`${API}/screening-questions/answers`, {
        credentials: "include",
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || []);
        setAnswers(data.answers || {});
      }
    } catch (error) {
      console.error("Error fetching screening questions:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const saveAnswers = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API}/screening-questions/answers`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ answers }),
      });
      
      if (response.ok) {
        toast.success("Screening answers saved!");
      } else {
        throw new Error("Failed to save");
      }
    } catch (error) {
      toast.error("Failed to save answers");
    } finally {
      setSaving(false);
    }
  };

  const addCustomQuestion = async () => {
    if (!newQuestion.trim() || !newAnswer.trim()) {
      toast.error("Please enter both question and answer");
      return;
    }

    try {
      const response = await fetch(`${API}/screening-questions/custom`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          question: newQuestion,
          answer: newAnswer,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAnswers(prev => ({
          ...prev,
          [data.question_id]: newAnswer
        }));
        setCustomQuestions(prev => [...prev, {
          id: data.question_id,
          question: newQuestion,
          answer: newAnswer,
          is_custom: true
        }]);
        setNewQuestion("");
        setNewAnswer("");
        setShowAddCustom(false);
        toast.success("Custom question added!");
      }
    } catch (error) {
      toast.error("Failed to add custom question");
    }
  };

  // Group questions by category
  const questionsByCategory = templates.reduce((acc, q) => {
    const category = q.category || "Other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(q);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    );
  }

  return (
    <Card className="border-white/10 bg-white/5">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
              <ClipboardList className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-lg">Screening Questions</CardTitle>
              <CardDescription>
                Pre-fill answers for common job application questions
              </CardDescription>
            </div>
          </div>
          <Button
            onClick={saveAnswers}
            disabled={saving}
            className="bg-purple-500 hover:bg-purple-600"
          >
            {saving ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            Save All
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Set your default answers to common screening questions. The browser extension will automatically fill these when you apply to jobs.
        </p>

        <Accordion type="multiple" className="space-y-2">
          {Object.entries(questionsByCategory).map(([category, questions]) => (
            <AccordionItem 
              key={category} 
              value={category}
              className="border border-white/10 rounded-lg px-4"
            >
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{category}</span>
                  <span className="text-xs text-muted-foreground">
                    ({questions.filter(q => answers[q.id]).length}/{questions.length} answered)
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="space-y-4 pt-2">
                {questions.map((q) => (
                  <div key={q.id} className="space-y-2">
                    <Label className="text-sm flex items-center gap-2">
                      {q.question}
                      {answers[q.id] && (
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                      )}
                    </Label>
                    
                    {q.type === "select" && q.options ? (
                      <Select
                        value={answers[q.id] || ""}
                        onValueChange={(value) => handleAnswerChange(q.id, value)}
                      >
                        <SelectTrigger className="bg-white/5 border-white/10">
                          <SelectValue placeholder="Select an answer..." />
                        </SelectTrigger>
                        <SelectContent>
                          {q.options.map((opt) => (
                            <SelectItem key={opt} value={opt}>
                              {opt}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        value={answers[q.id] || ""}
                        onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                        placeholder={`Enter your answer...`}
                        className="bg-white/5 border-white/10"
                      />
                    )}
                    
                    {q.keywords && (
                      <p className="text-xs text-muted-foreground">
                        Matches: {q.keywords.slice(0, 3).join(", ")}...
                      </p>
                    )}
                  </div>
                ))}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>

        {/* Custom Questions Section */}
        <div className="pt-4 border-t border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium">Custom Questions</h3>
            <Dialog open={showAddCustom} onOpenChange={setShowAddCustom}>
              <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="border-white/10">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Custom Question
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Custom Question</DialogTitle>
                  <DialogDescription>
                    Add a question you've seen on job applications that isn't in the standard list.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label>Question</Label>
                    <Textarea
                      value={newQuestion}
                      onChange={(e) => setNewQuestion(e.target.value)}
                      placeholder="e.g., Do you have experience with Kubernetes?"
                      className="bg-white/5 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Your Answer</Label>
                    <Input
                      value={newAnswer}
                      onChange={(e) => setNewAnswer(e.target.value)}
                      placeholder="e.g., Yes, 3 years"
                      className="bg-white/5 border-white/10"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setShowAddCustom(false)}>
                    Cancel
                  </Button>
                  <Button onClick={addCustomQuestion} className="bg-purple-500 hover:bg-purple-600">
                    Add Question
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {customQuestions.length > 0 ? (
            <div className="space-y-3">
              {customQuestions.map((q) => (
                <div 
                  key={q.id} 
                  className="p-3 rounded-lg bg-white/5 border border-white/10"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-sm font-medium">{q.question}</p>
                      <p className="text-sm text-emerald-400 mt-1">→ {q.answer}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center py-4">
              No custom questions added yet. Click "Add Custom Question" to add one.
            </p>
          )}
        </div>

        {/* Tips */}
        <div className="p-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 mt-4">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-indigo-400 mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-indigo-400">How it works</p>
              <p className="text-muted-foreground mt-1">
                When you use the browser extension to auto-fill a job application, 
                it will match questions on the form to your saved answers using keyword matching.
                The more questions you answer here, the more the extension can fill automatically.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

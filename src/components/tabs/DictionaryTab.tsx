import React, { useState } from "react";
import { BookA, Plus, X, Sparkles, Check, Info } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

interface DictionaryTabProps {
  dictionary: string[];
  onUpdateDictionary: (words: string[]) => void;
}

export function DictionaryTab({ dictionary, onUpdateDictionary }: DictionaryTabProps) {
  const [newWord, setNewWord] = useState("");

  const handleAdd = () => {
    const raw = newWord.trim();
    if (!raw) return;

    // Split by comma, semicolon, or newline to support batch pasting
    const candidates = raw
      .split(/[,;\n]+/)
      .map((w) => w.trim().replace(/^["'“‘]+|["'”’]+$/g, ""))
      .filter((w) => w.length > 0);

    if (candidates.length === 0) return;

    const existingLower = new Set(dictionary.map((w) => w.toLowerCase()));
    const toAdd: string[] = [];
    const duplicates: string[] = [];

    for (const cand of candidates) {
      const lower = cand.toLowerCase();
      if (existingLower.has(lower) || toAdd.some((a) => a.toLowerCase() === lower)) {
        duplicates.push(cand);
      } else {
        toAdd.push(cand);
      }
    }

    if (toAdd.length === 0) {
      toast.error(
        duplicates.length === 1
          ? `"${duplicates[0]}" is already in your dictionary.`
          : `All ${duplicates.length} terms are already in your dictionary.`
      );
      return;
    }

    const updated = [...dictionary, ...toAdd];
    onUpdateDictionary(updated);
    setNewWord("");

    if (toAdd.length === 1) {
      toast.success(`Added "${toAdd[0]}" to dictionary`);
    } else {
      toast.success(`Added ${toAdd.length} terms to dictionary`);
    }

    if (duplicates.length > 0) {
      toast.info(`Skipped ${duplicates.length} duplicate ${duplicates.length === 1 ? "term" : "terms"}`);
    }
  };

  const handleRemove = (word: string) => {
    const updated = dictionary.filter((w) => w !== word);
    onUpdateDictionary(updated);
    toast.info(`Removed "${word}"`);
  };

  return (
    <div className="space-y-4">
      {/* Add New Word Header Card */}
      <Card className="p-4 bg-neutral-900/60 border-white/5 rounded-2xl">
        <div className="flex flex-col gap-1.5 mb-3">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <BookA className="w-4 h-4 text-neutral-300" />
            Custom Dictionary & Jargon
          </h3>
          <p className="text-xs text-neutral-400 leading-relaxed">
            Teach Hush names, company jargon, acronyms, or technical terms that Whisper
            frequently misspells. Words added here are prioritized during transcription.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Input
            value={newWord}
            onChange={(e) => setNewWord(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAdd();
              }
            }}
            placeholder="Add terms (e.g. Suryansh, Kubernetes, API - comma-separated)…"
            className="bg-neutral-950/80 border-white/10 rounded-full h-9 text-xs"
          />
          <Button
            onClick={handleAdd}
            disabled={!newWord.trim()}
            size="sm"
            className="gap-1.5 h-9 px-4 rounded-full font-semibold shrink-0"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Word</span>
          </Button>
        </div>
      </Card>

      {/* Words List Card */}
      <Card className="p-4 bg-neutral-900/60 border-white/5 rounded-2xl">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-neutral-300 uppercase tracking-wider">
            Active Dictionary ({dictionary.length} {dictionary.length === 1 ? "word" : "words"})
          </span>
          <span className="text-[11px] text-neutral-500">
            Fuzzy-matched & post-corrected
          </span>
        </div>

        {dictionary.length === 0 ? (
          <div className="p-8 text-center border border-dashed border-white/10 rounded-xl">
            <p className="text-xs text-neutral-400">
              No custom terms added yet. Add names, slang, or technical jargon above.
            </p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto p-1">
            {dictionary.map((word) => (
              <div
                key={word}
                className="flex items-center gap-1.5 bg-neutral-800/80 hover:bg-neutral-800 text-neutral-200 px-3 py-1.5 rounded-full text-xs font-medium border border-white/5 transition-all group"
              >
                <span>{word}</span>
                <button
                  onClick={() => handleRemove(word)}
                  className="w-4 h-4 rounded-full flex items-center justify-center text-neutral-400 hover:text-white hover:bg-neutral-700 transition-colors"
                  title={`Remove ${word}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Informative Guidance Card */}
      <Card className="p-4 bg-neutral-900/30 border-white/5 rounded-2xl flex items-start gap-3">
        <Info className="w-4 h-4 text-neutral-400 shrink-0 mt-0.5" />
        <div className="text-xs text-neutral-400 space-y-1">
          <p className="font-medium text-neutral-300">How does Custom Dictionary work?</p>
          <p>
            1. <strong>Prompt bias:</strong> Whisper is seeded with your custom terms before speech begins, increasing the model's likelihood of recognizing rare proper nouns.
          </p>
          <p>
            2. <strong>Fuzzy post-correction:</strong> Phonetic slips or spelling mangles (e.g. "Siryanch" for "Suryansh") are automatically replaced with your canonical spelling.
          </p>
        </div>
      </Card>
    </div>
  );
}

"use client";

import { useRef, useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogDescription,
} from "@/components/ui/dialog";
import { uploadPaper } from "@/lib/api";
import { toast } from "sonner";

export function UploadDialog({ onUploaded }: { onUploaded: () => void }) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File | undefined) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("only pdf files are accepted");
      return;
    }
    setBusy(true);
    try {
      const result = await uploadPaper(file);
      toast.success(`added "${result.title}" (${result.chunks} chunks across ${result.pages} pages)`);
      setOpen(false);
      onUploaded();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button className="w-full rounded-2xl gap-2 transition-transform hover:scale-[1.03] active:scale-95" />
        }
      >
        <Upload className="size-4" />
        Add a paper
      </DialogTrigger>
      <DialogContent className="rounded-3xl animate-in zoom-in-95 fade-in duration-200">
        <DialogHeader>
          <DialogTitle className="font-heading">Upload a paper</DialogTitle>
          <DialogDescription>
            Drop a PDF in and paperpilot will chunk it page by page so every
            answer can point back to exactly where it came from.
          </DialogDescription>
        </DialogHeader>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            handleFile(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          className={`flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-10 text-center cursor-pointer transition-all duration-200 ${
            dragging
              ? "scale-[1.02] border-primary bg-accent/40"
              : "border-border hover:bg-muted/50"
          }`}
        >
          {busy ? (
            <Loader2 className="size-8 animate-spin text-primary" />
          ) : (
            <Upload className="size-8 text-muted-foreground animate-float" />
          )}
          <p className="text-sm text-muted-foreground">
            {busy ? "Reading your paper..." : "Drag a PDF here, or click to browse"}
          </p>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
        </div>
      </DialogContent>
    </Dialog>
  );
}

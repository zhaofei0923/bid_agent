"use client"

import { memo, useState, useCallback, useRef } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/hooks/use-documents"
import { Button } from "@/components/ui/button"
import { Card, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useTranslations } from "next-intl"
import { Trash2 } from "lucide-react"

interface UploadStepProps {
  projectId: string
}

export const UploadStep = memo(function UploadStep({
  projectId,
}: UploadStepProps) {
  const { completeStep, goToStep } = useBidWorkspaceStore()
  const t = useTranslations("bid")
  const { data: documents } = useDocuments(projectId)
  const uploadMutation = useUploadDocument(projectId)
  const deleteMutation = useDeleteDocument(projectId)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDelete = useCallback(
    async (documentId: string) => {
      if (!window.confirm("确定要删除这个文件吗？")) return
      setDeletingId(documentId)
      try {
        await deleteMutation.mutateAsync(documentId)
      } catch {
        // silent — list will not update on error
      } finally {
        setDeletingId(null)
      }
    },
    [deleteMutation]
  )

  const handleFileSelect = useCallback(
    async (files: FileList | null) => {
      if (!files?.length) return
      setUploadError(null)
      for (const file of Array.from(files)) {
        if (
          file.type === "application/pdf" ||
          file.type ===
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ) {
          try {
            await uploadMutation.mutateAsync(file)
          } catch (err: unknown) {
            const msg =
              err instanceof Error ? err.message : "上传失败，请重试"
            setUploadError(msg)
          }
        } else {
          setUploadError(`不支持的文件类型: ${file.name}，仅支持 PDF / DOCX`)
        }
      }
    },
    [uploadMutation]
  )

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      handleFileSelect(e.dataTransfer.files)
    },
    [handleFileSelect]
  )

  const handleNext = () => {
    completeStep("upload")
    goToStep("overview")
  }

  /** Derive a simple file type label from the filename extension */
  const getFileTypeIcon = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase()
    return ext === "pdf" ? "📕" : "📘"
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">{t("upload.title")}</h2>
        <p className="text-muted-foreground text-sm mt-1">
          {t("upload.subtitle")}
        </p>
      </div>

      {/* Upload area */}
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setIsDragging(true)
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50"
        }`}
      >
        <div className="text-4xl mb-4">📄</div>
        <p className="text-sm font-medium mb-1">
          {t("upload.dragHint")}
        </p>
        <p className="text-xs text-muted-foreground mb-4">
          {t("upload.formatHint")}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          multiple
          className="hidden"
          onChange={(e) => {
            handleFileSelect(e.target.files)
            // Reset input so the same file can be re-selected after an error
            e.target.value = ""
          }}
        />
        <Button
          variant="outline"
          size="sm"
          disabled={uploadMutation.isPending}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploadMutation.isPending ? t("upload.uploading") : t("upload.selectFile")}
        </Button>
        {uploadMutation.isPending && (
          <p className="mt-4 text-sm text-muted-foreground animate-pulse">
            {t("upload.uploading")}
          </p>
        )}
        {uploadError && (
          <p className="mt-4 text-sm text-destructive">⚠️ {uploadError}</p>
        )}
      </div>

      {/* Document list */}
      {documents && documents.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">{t("upload.uploadedFiles")}</h3>
          {documents.map((doc) => (
            <Card key={doc.id}>
              <CardHeader className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-lg flex-shrink-0">
                      {getFileTypeIcon(doc.original_filename || doc.filename)}
                    </span>
                    <span className="text-sm font-medium truncate">
                      {doc.original_filename || doc.filename}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant="secondary">{doc.status}</Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-destructive"
                      disabled={deletingId === doc.id}
                      onClick={() => handleDelete(doc.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
            </Card>
          ))}
        </div>
      )}

      {/* Next button */}
      {documents && documents.length > 0 && (
        <div className="flex justify-end">
          <Button onClick={handleNext}>
            {t("upload.nextStep")}
          </Button>
        </div>
      )}
    </div>
  )
})

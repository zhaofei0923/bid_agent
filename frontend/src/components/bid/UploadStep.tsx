"use client"

import { memo, useState, useCallback, useRef } from "react"
import { useBidWorkspaceStore } from "@/stores/bid-workspace"
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/hooks/use-documents"
import { Button } from "@/components/ui/button"
import { Card, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { useTranslations } from "next-intl"
import { Trash2, Loader2 } from "lucide-react"

interface UploadStepProps {
  projectId: string
}

const STATUS_LABELS: Record<string, string> = {
  pending: "待处理",
  processing: "解析中",
  processed: "已就绪",
  completed: "已就绪",
  error: "失败",
}

const STATUS_VARIANTS: Record<string, "secondary" | "outline" | "default" | "destructive"> = {
  pending: "secondary",
  processing: "secondary",
  processed: "default",
  completed: "default",
  error: "destructive",
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

  const hasProcessingDocs = documents?.some(
    (d) => d.status === "pending" || d.status === "processing"
  ) ?? false

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
                    <div className="min-w-0">
                      <span className="text-sm font-medium truncate block">
                        {doc.original_filename || doc.filename}
                      </span>
                      {(doc.status === "processing" || doc.status === "pending") && (
                        <div className="mt-1 flex items-center gap-2">
                          <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                          <Progress
                            value={doc.processing_progress || 0}
                            className="h-1.5 w-24"
                          />
                          <span className="text-xs text-muted-foreground">
                            {doc.processing_progress || 0}%
                          </span>
                        </div>
                      )}
                      {doc.error_message && (
                        <p className="text-xs text-destructive mt-0.5 truncate">
                          {doc.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge variant={STATUS_VARIANTS[doc.status] || "secondary"}>
                      {STATUS_LABELS[doc.status] || doc.status}
                    </Badge>
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

      {/* Status hint for processing documents */}
      {hasProcessingDocs && (
        <p className="text-sm text-muted-foreground flex items-center gap-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          文件正在后台解析向量化，完成后可进入下一步
        </p>
      )}

      {/* Next button */}
      {documents && documents.length > 0 && (
        <div className="flex justify-end">
          <Button onClick={handleNext} disabled={hasProcessingDocs}>
            {hasProcessingDocs ? "等待处理完成..." : t("upload.nextStep")}
          </Button>
        </div>
      )}
    </div>
  )
})

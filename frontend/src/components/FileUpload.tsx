import { useRef, useState, type ChangeEvent, type DragEvent } from 'react'

interface FileUploadProps {
  id: string
  label: string
  hint: string
  accept: string
  file: File | null
  onChange: (file: File | null) => void
}

export function FileUpload({ id, label, hint, accept, file, onChange }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  function handleFiles(selected: FileList | null) {
    const nextFile = selected?.[0] ?? null
    onChange(nextFile)
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleFiles(event.target.files)
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setDragging(false)
    handleFiles(event.dataTransfer.files)
  }

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <div
        className={`upload-zone ${dragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            inputRef.current?.click()
          }
        }}
        role="button"
        tabIndex={0}
        aria-label={`Upload ${label}`}
      >
        <input
          ref={inputRef}
          id={id}
          type="file"
          accept={accept}
          className="sr-only"
          onChange={onInputChange}
        />
        {file ? (
          <>
            <p className="upload-title">{file.name}</p>
            <p className="upload-meta">{(file.size / 1024).toFixed(1)} KB · click to replace</p>
          </>
        ) : (
          <>
            <p className="upload-title">Drop a file here or click to browse</p>
            <p className="upload-meta">{hint}</p>
          </>
        )}
      </div>
    </div>
  )
}

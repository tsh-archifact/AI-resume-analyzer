import { useState, type FormEvent } from 'react'

import { rewriteResume } from '../api/resume'
import { ApiRequestError } from '../api/client'
import { FileUpload } from '../components/FileUpload'
import { useAuth } from '../context/AuthContext'

const RESUME_ACCEPT = '.pdf,.doc,.docx'
const JD_ACCEPT = '.pdf,.doc,.docx,.txt,.png,.jpg,.jpeg'

export function RewritePage() {
  const { token } = useAuth()
  const [resume, setResume] = useState<File | null>(null)
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [jdText, setJdText] = useState('')
  const [jdMode, setJdMode] = useState<'text' | 'file'>('text')
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSuccessMessage(null)

    if (!resume) {
      setError('Please upload a resume file.')
      return
    }

    if (jdMode === 'file' && !jdFile) {
      setError('Please upload a job description file or switch to pasted text.')
      return
    }

    if (jdMode === 'text' && !jdText.trim()) {
      setError('Please paste a job description or switch to file upload.')
      return
    }

    if (!token) {
      setError('You must be signed in to rewrite resumes.')
      return
    }

    setSubmitting(true)

    try {
      const { blob, filename } = await rewriteResume(
        {
          resume,
          jobDescriptionFile: jdMode === 'file' ? jdFile : null,
          jobDescriptionText: jdMode === 'text' ? jdText : undefined,
        },
        token,
      )

      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      anchor.click()
      URL.revokeObjectURL(url)

      setSuccessMessage(`Download started: ${filename}`)
    } catch (caught) {
      const message =
        caught instanceof ApiRequestError
          ? caught.message
          : 'Rewrite failed. Please try again.'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="container workspace-page">
      <header className="page-header">
        <div>
          <p className="eyebrow">Tailored rewrite</p>
          <h1>Generate a job-aligned resume</h1>
          <p className="lead">
            The rewrite endpoint uses your configured LLM to produce a truthful, role-specific DOCX
            download. If the LLM is unavailable, the API returns a clear 503 error.
          </p>
        </div>
      </header>

      <div className="workspace-grid rewrite-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <FileUpload
            id="rewrite-resume"
            label="Resume"
            hint="PDF, DOC, or DOCX"
            accept={RESUME_ACCEPT}
            file={resume}
            onChange={setResume}
          />

          <fieldset className="mode-toggle">
            <legend>Job description input</legend>
            <label>
              <input
                type="radio"
                name="rewrite-jd-mode"
                checked={jdMode === 'text'}
                onChange={() => setJdMode('text')}
              />
              Paste text
            </label>
            <label>
              <input
                type="radio"
                name="rewrite-jd-mode"
                checked={jdMode === 'file'}
                onChange={() => setJdMode('file')}
              />
              Upload file
            </label>
          </fieldset>

          {jdMode === 'text' ? (
            <div className="field">
              <label htmlFor="rewrite-jd-text">Job description</label>
              <textarea
                id="rewrite-jd-text"
                rows={10}
                placeholder="Paste the role requirements and responsibilities…"
                value={jdText}
                onChange={(event) => setJdText(event.target.value)}
              />
            </div>
          ) : (
            <FileUpload
              id="rewrite-jd"
              label="Job description file"
              hint="PDF, DOC, DOCX, TXT, PNG, JPG, or JPEG"
              accept={JD_ACCEPT}
              file={jdFile}
              onChange={setJdFile}
            />
          )}

          {error ? <p className="form-error">{error}</p> : null}
          {successMessage ? <p className="form-success">{successMessage}</p> : null}

          <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
            {submitting ? 'Generating DOCX…' : 'Download rewritten resume'}
          </button>
        </form>

        <aside className="panel info-panel">
          <h2>What to expect</h2>
          <ul className="info-list">
            <li>The backend extracts resume and job-description text before rewriting.</li>
            <li>The LLM keeps your experience truthful while aligning language to the role.</li>
            <li>The response is a downloadable DOCX named <code>rewritten_resume.docx</code>.</li>
            <li>Ensure your API key and model are configured in the backend <code>.env</code>.</li>
          </ul>
        </aside>
      </div>
    </div>
  )
}

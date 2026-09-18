import type { ResumeTemplateInfo } from '../api/resume'

interface TemplateSelectorProps {
  templates: ResumeTemplateInfo[]
  selectedTemplate: string
  onSelectTemplate: (templateId: string) => void
  disabled?: boolean
}

export function TemplateSelector({
  templates,
  selectedTemplate,
  onSelectTemplate,
  disabled = false,
}: TemplateSelectorProps) {
  const activeTemplate = templates.find((t) => t.template_id === selectedTemplate)

  return (
    <div className="template-picker-section">
      <div className="template-picker-header">
        <div>
          <h3 className="marker-blue-title" style={{ margin: 0, fontSize: '1.15rem' }}>
            🎨 Select DOCX Template Style
          </h3>
          <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Pick one of 5 ATS-compliant formatting designs for your exported Word document.
          </p>
        </div>
        {activeTemplate && (
          <div className="template-active-badge">
            Selected: <strong>{activeTemplate.name}</strong>
          </div>
        )}
      </div>

      <div className="template-grid">
        {templates.map((tpl) => {
          const isSelected = tpl.template_id === selectedTemplate
          return (
            <div
              key={tpl.template_id}
              className={`template-card ${isSelected ? 'template-card-selected' : ''} ${disabled ? 'template-card-disabled' : ''}`}
              onClick={() => {
                if (!disabled) {
                  onSelectTemplate(tpl.template_id)
                }
              }}
              role="button"
              tabIndex={disabled ? -1 : 0}
              onKeyDown={(e) => {
                if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
                  onSelectTemplate(tpl.template_id)
                }
              }}
            >
              <div className="template-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span
                    className="template-swatch"
                    style={{ backgroundColor: tpl.accent_hex }}
                    title={`Accent: ${tpl.accent_hex}`}
                  />
                  <span className="template-name">{tpl.name}</span>
                </div>
                {isSelected && <span className="template-check">✓ Active</span>}
              </div>
              <div className="template-meta">
                <span className="template-font-tag">Font: {tpl.font_family}</span>
                <span className="template-persona-tag">{tpl.persona}</span>
              </div>
              <p className="template-desc">{tpl.description}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

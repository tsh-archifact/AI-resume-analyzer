interface SkillTagsProps {
  title: string
  skills: string[]
  variant: 'matched' | 'missing' | 'neutral'
}

export function SkillTags({ title, skills, variant }: SkillTagsProps) {
  return (
    <section className="skill-panel">
      <div className="skill-panel-header">
        <h3>{title}</h3>
        <span className="count-badge">{skills.length}</span>
      </div>
      {skills.length === 0 ? (
        <p className="empty-note">No skills detected.</p>
      ) : (
        <ul className={`tag-list tag-list-${variant}`}>
          {skills.map((skill) => (
            <li key={skill}>{skill}</li>
          ))}
        </ul>
      )}
    </section>
  )
}

type FileUploaderProps = {
  onChange: (files: FileList | null) => void
}

export function FileUploader({ onChange }: FileUploaderProps) {
  return (
    <input
      type="file"
      accept=".txt,.md,.pdf,.docx"
      multiple
      onChange={(event) => onChange(event.target.files)}
    />
  )
}

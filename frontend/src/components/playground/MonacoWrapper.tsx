import Editor from "@monaco-editor/react";

export default function MonacoWrapper({
  value,
  onChange,
  language = "json",
  height = 200,
}: {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  height?: number;
}) {
  return (
    <Editor
      height={height}
      language={language}
      value={value}
      onChange={(val) => onChange(val || "")}
      options={{
        minimap: { enabled: false },
        fontSize: 13,
        lineNumbers: "on",
        scrollBeyondLastLine: false,
      }}
    />
  );
}

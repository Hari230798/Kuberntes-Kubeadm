{{- define "dataprotector.backendImage" -}}
{{ .Values.image.registry }}/{{ .Values.image.repositoryPrefix }}/{{ .Values.backend.image }}:{{ .Values.image.tag }}
{{- end -}}

{{- define "dataprotector.frontendImage" -}}
{{ .Values.image.registry }}/{{ .Values.image.repositoryPrefix }}/{{ .Values.frontend.image }}:{{ .Values.image.tag }}
{{- end -}}

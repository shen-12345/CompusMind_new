import request from './request'

export function startApplication(policyId: number) {
  return request.post(`/applications/start?policy_id=${policyId}`)
}

export function uploadMaterial(applicationId: number, materialName: string, file: File) {
  const formData = new FormData()
  formData.append('material_name', materialName)
  formData.append('file', file)
  return request.post(`/applications/${applicationId}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteMaterial(applicationId: number, materialName: string) {
  return request.delete(`/applications/${applicationId}/material?material_name=${materialName}`)
}

export function submitApplication(applicationId: number) {
  return request.post(`/applications/${applicationId}/submit`)
}

export function abandonApplication(applicationId: number) {
  return request.post(`/applications/${applicationId}/abandon`)
}

export function getApplications() {
  return request.get('/applications')
}

export function getApplicationDetail(applicationId: number) {
  return request.get(`/applications/${applicationId}`)
}
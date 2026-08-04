import request from '../request'

export function getImportTemplate(): Promise<Blob> {
  return request.get('/admin/users/import/template', { responseType: 'blob' })
}

export function uploadImport(formData: FormData): Promise<any> {
  return request.post('/admin/users/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
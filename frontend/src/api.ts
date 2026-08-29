import axios from 'axios'
export const api = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api' })
export const postRecords = (path: string, records: Record<string, unknown>[]) => api.post(path, { records })

import { apiFetch } from './client'
import type { TokenResponse, User } from '../types/api'

export async function login(username: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username, password })

  return apiFetch<TokenResponse>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body,
  })
}

export async function register(username: string, password: string): Promise<User> {
  return apiFetch<User>('/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  })
}

export async function getCurrentUser(token: string): Promise<User> {
  return apiFetch<User>('/auth/me', {}, token)
}

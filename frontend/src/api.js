/**
 * Centralized API Client for NexusAI Backend
 */

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const getAuthHeader = () => {
    const token = localStorage.getItem('nexus_access_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export async function loginWithPassword(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_BASE}/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString()
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Authentication failed' }));
        throw new Error(error.detail || 'Login failed');
    }

    return response.json();
}

export async function fetchChatHistory() {
    const response = await fetch(`${API_BASE}/chat/history`, {
        headers: getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to fetch history');
    return response.json();
}

export async function clearChatHistory() {
    const response = await fetch(`${API_BASE}/chat/history`, {
        method: 'DELETE',
        headers: getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to clear history');
    return response.json();
}

export async function sendChatMessage(message, mode = 'auto') {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...getAuthHeader()
        },
        body: JSON.stringify({ message, mode })
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to send message' }));
        throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
}

export async function uploadPdfFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'POST',
        headers: getAuthHeader(),
        body: formData
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'PDF Upload failed' }));
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

export async function deletePdfFile() {
    const response = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'DELETE',
        headers: getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to delete PDF');
    return response.json();
}

export async function fetchPdfStatus() {
    const response = await fetch(`${API_BASE}/upload-pdf`, {
        headers: getAuthHeader()
    });
    if (!response.ok) return { has_file: false };
    return response.json();
}

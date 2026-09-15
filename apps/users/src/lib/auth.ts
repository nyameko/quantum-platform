export type AllauthFlow = {
  id?: string;
  provider?: string;
  is_pending?: boolean;
};

export type AllauthPayload = {
  status?: number;
  data?: {
    user?: {
      id?: number;
      email?: string;
      username?: string;
    };
    flows?: AllauthFlow[];
  };
  meta?: {
    is_authenticated?: boolean;
  };
  errors?: Array<{
    message?: string;
    code?: string;
    param?: string;
  }>;
};

function getCookie(name: string): string | null {
  const item = document.cookie
    .split('; ')
    .find((part) => part.startsWith(`${name}=`));

  if (!item) return null;

  return decodeURIComponent(item.slice(name.length + 1));
}

export async function ensureCsrf(): Promise<void> {
  await fetch('/api/v1/csrf/', {
    method: 'GET',
    credentials: 'same-origin',
  });
}

export async function csrfJsonFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  await ensureCsrf();

  const headers = new Headers(init.headers);
  const token = getCookie('csrftoken');

  if (token) {
    headers.set('X-CSRFToken', token);
  }

  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  return fetch(input, {
    ...init,
    headers,
    credentials: 'same-origin',
  });
}

export async function readPayload(
  response: Response,
): Promise<AllauthPayload> {
  return response.json().catch(() => ({}));
}

export async function getSession(): Promise<{
  response: Response;
  payload: AllauthPayload;
}> {
  const response = await fetch(
    '/_allauth/browser/v1/auth/session',
    {
      method: 'GET',
      credentials: 'same-origin',
    },
  );

  return {
    response,
    payload: await readPayload(response),
  };
}

export function hasPendingFlow(
  payload: AllauthPayload,
  flowId: string,
): boolean {
  const flows = payload.data?.flows ?? [];

  return flows.some(
    (flow) =>
      flow.id === flowId &&
      flow.is_pending !== false,
  );
}

export function firstError(
  payload: AllauthPayload,
  fallback: string,
): string {
  return payload.errors?.[0]?.message ?? fallback;
}

export async function logout(): Promise<void> {
  await csrfJsonFetch(
    '/_allauth/browser/v1/auth/session',
    {
      method: 'DELETE',
    },
  );
}

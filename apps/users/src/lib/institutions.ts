export interface Institution {
  code: string;
  label: string;
}

export async function loadInstitutions(): Promise<Institution[]> {
  const response = await fetch('/api/v1/institutions/', {
    credentials: 'same-origin',
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error('Unable to load institutions.');
  }

  return response.json();
}

function esc(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('"', '&quot;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}

export function populateInstitutionSelect(
  select: HTMLSelectElement,
  institutions: Institution[],
  selected = '',
) {
  select.innerHTML = [
    '<option value="">Select primary institution</option>',
    ...institutions.map(({ code, label }) => {
      const isSelected = code === selected ? ' selected' : '';
      return `<option value="${esc(code)}"${isSelected}>${esc(label)}</option>`;
    }),
  ].join('');
}

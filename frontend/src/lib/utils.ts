import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(date: string | Date): string {
  return new Date(date).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatSalary(min?: number, max?: number): string {
  if (!min && !max) return 'Salary not specified';
  if (min && !max) return `$${min.toLocaleString()}+`;
  if (!min && max) return `Up to $${max.toLocaleString()}`;
  return `$${min?.toLocaleString()} - $${max?.toLocaleString()}`;
}

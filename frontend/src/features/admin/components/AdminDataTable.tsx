import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { PaginatedResponse } from '../types';

interface AdminDataTableProps<T> {
  data: PaginatedResponse<T> | undefined;
  isLoading: boolean;
  columns: {
    header: string;
    key: string;
    render?: (item: T) => React.ReactNode;
  }[];
  renderRow: (item: T) => React.ReactNode;
  onPageChange?: (page: number) => void;
  emptyMessage?: string;
  emptyIcon?: React.ReactNode;
}

export function AdminDataTable<T>({
  data,
  isLoading,
  columns,
  renderRow,
  onPageChange,
  emptyMessage = 'No data found',
  emptyIcon,
}: AdminDataTableProps<T>) {
  const currentPage = data?.previous ? parseInt(new URL(data.previous).searchParams.get('page') || '1') + 1 : 1;
  const totalPages = data ? Math.ceil(data.count / (data.results.length || 10)) : 1;

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-16 bg-slate-800/50 rounded animate-pulse" />
        ))}
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="text-center py-12">
        {emptyIcon}
        <p className="text-slate-400 mt-4">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800">
              {columns.map((column) => (
                <TableHead key={column.key}>{column.header}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.results.map((item, index) => (
              <TableRow key={index} className="border-slate-800">
                {renderRow(item)}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {onPageChange && totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-slate-400">
            Showing {data.results.length} of {data.count} results
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="border-slate-700"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </Button>
            <span className="text-sm text-slate-400">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="border-slate-700"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

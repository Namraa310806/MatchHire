import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

interface AdminActionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  targetInfo: React.ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
  reason: string;
  onReasonChange: (reason: string) => void;
  showReason?: boolean;
  confirmButtonText?: string;
  danger?: boolean;
}

export function AdminActionDialog({
  open,
  onOpenChange,
  title,
  description,
  targetInfo,
  onConfirm,
  onCancel,
  isPending,
  reason,
  onReasonChange,
  showReason = true,
  confirmButtonText = 'Confirm',
  danger = false,
}: AdminActionDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="border-slate-800 bg-slate-900">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {targetInfo}
          {showReason && (
            <div className="space-y-2">
              <Label>Reason</Label>
              <Textarea
                placeholder="Provide a reason for this action..."
                value={reason}
                onChange={(e) => onReasonChange(e.target.value)}
                className="border-slate-700 bg-slate-800/50 min-h-24"
              />
            </div>
          )}
        </div>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={onCancel}
            className="border-slate-700"
          >
            Cancel
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isPending || (showReason && !reason.trim())}
            className={danger ? 'bg-red-500 hover:bg-red-600' : ''}
          >
            {isPending ? 'Processing...' : confirmButtonText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

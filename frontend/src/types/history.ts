import type { ApprovalStep, RequestStatus } from './request'
import type { UserSummary } from './user'

export type ApprovalAction =
  | 'Submit'
  | 'FirstApprove'
  | 'FirstReject'
  | 'SecondApprove'
  | 'SecondReject'

export interface HistoryEntry {
  id: string
  action: ApprovalAction
  operator: UserSummary
  step: ApprovalStep | null
  comment: string | null
  previousStatus: RequestStatus | null
  previousStep: ApprovalStep | null
  newStatus: RequestStatus
  newStep: ApprovalStep | null
  createdAt: string
}

export const APPROVAL_ACTION_LABEL: Record<ApprovalAction, string> = {
  Submit: '提交申请',
  FirstApprove: '一级审批通过',
  FirstReject: '一级审批驳回',
  SecondApprove: '二级审批通过',
  SecondReject: '二级审批驳回',
}

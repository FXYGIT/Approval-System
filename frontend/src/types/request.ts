import type { UserSummary } from './user'

export type RequestStatus = 'Draft' | 'InProgress' | 'Approved' | 'Rejected'

export type ApprovalStep = 'First' | 'Second'

export interface RequestPublic {
  id: string
  title: string
  content: string
  applicantId: string
  firstApproverId: string
  secondApproverId: string
  applicant: UserSummary
  firstApprover: UserSummary
  secondApprover: UserSummary
  status: RequestStatus
  currentStep: ApprovalStep | null
  version: number
  createdAt: string
  updatedAt: string
  submittedAt: string | null
}

export interface DraftInput {
  title: string
  content: string
  firstApproverId: string
  secondApproverId: string
}

export interface DraftUpdate extends DraftInput {
  version: number
}

export const REQUEST_STATUS_LABEL: Record<RequestStatus, string> = {
  Draft: '草稿',
  InProgress: '审批中',
  Approved: '已通过',
  Rejected: '已驳回',
}

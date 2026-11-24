import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ElMessage } from 'element-plus'
import { approveRequest, rejectRequest } from '@/api/requests'
import { ApiError } from '@/api/http'
import ApprovalActions from '@/components/ApprovalActions.vue'
import type { RequestPublic } from '@/types/request'

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    default: actual.default,
    ElMessage: { success: vi.fn(), error: vi.fn(), warning: vi.fn() },
  }
})

vi.mock('@/api/requests', () => ({
  approveRequest: vi.fn(),
  rejectRequest: vi.fn(),
}))

const applicantId = 'u-applicant'
const approver1 = 'u-approver1'
const approver2 = 'u-approver2'

function request(partial: Partial<RequestPublic> = {}): RequestPublic {
  return {
    id: 'r1',
    title: '测试申请',
    content: '内容',
    applicantId,
    firstApproverId: approver1,
    secondApproverId: approver2,
    applicant: { id: applicantId, username: 'me', displayName: 'Me' },
    firstApprover: { id: approver1, username: 'a1', displayName: 'A1' },
    secondApprover: { id: approver2, username: 'a2', displayName: 'A2' },
    status: 'InProgress',
    currentStep: 'First',
    version: 1,
    createdAt: '2026-01-01T00:00:00Z',
    updatedAt: '2026-01-01T00:00:00Z',
    submittedAt: '2026-01-01T00:00:00Z',
    ...partial,
  }
}

function mountActions(req: RequestPublic, currentUserId = approver1) {
  return mount(ApprovalActions, {
    props: { request: req, currentUserId },
    global: { plugins: [ElementPlus] },
  })
}

function findButton(wrapper: ReturnType<typeof mountActions>, text: string) {
  return wrapper.findAll('button').find((b) => b.text().includes(text))
}

describe('ApprovalActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(approveRequest).mockResolvedValue(request())
    vi.mocked(rejectRequest).mockResolvedValue(request())
  })

  it('hides actions for non-current approver', () => {
    const wrapper = mountActions(request({ currentStep: 'First' }), applicantId)
    expect(wrapper.find('.approval-actions').exists()).toBe(false)
  })

  it('hides actions when request is no longer in progress', () => {
    const wrapper = mountActions(request({ status: 'Approved', currentStep: null }), approver1)
    expect(wrapper.find('.approval-actions').exists()).toBe(false)
  })

  it('shows actions for first approver on first step', () => {
    const wrapper = mountActions(request({ currentStep: 'First' }), approver1)
    expect(wrapper.text()).toContain('审批通过')
    expect(wrapper.text()).toContain('驳回')
  })

  it('shows actions for second approver on second step', () => {
    const wrapper = mountActions(request({ currentStep: 'Second' }), approver2)
    expect(wrapper.find('.approval-actions').exists()).toBe(true)
  })

  it('approves and emits done', async () => {
    const wrapper = mountActions(request({ currentStep: 'First' }), approver1)
    await findButton(wrapper, '审批通过')!.trigger('click')
    await flushPromises()
    await findButton(wrapper, '确认通过')!.trigger('click')
    await flushPromises()

    expect(approveRequest).toHaveBeenCalledWith('r1', { comment: null, version: 1 })
    expect(wrapper.emitted('done')).toBeTruthy()
    expect(ElMessage.success).toHaveBeenCalled()
  })

  it('requires comment when rejecting', async () => {
    const wrapper = mountActions(request({ currentStep: 'First' }), approver1)
    await findButton(wrapper, '驳回')!.trigger('click')
    await flushPromises()
    await findButton(wrapper, '确认驳回')!.trigger('click')
    await flushPromises()

    expect(rejectRequest).not.toHaveBeenCalled()
    expect(ElMessage.warning).toHaveBeenCalled()
  })

  it('rejects with comment and emits done', async () => {
    const wrapper = mountActions(request({ currentStep: 'Second' }), approver2)
    await findButton(wrapper, '驳回')!.trigger('click')
    await flushPromises()

    const textarea = wrapper.find('textarea')
    await textarea.setValue('材料不完整')
    await findButton(wrapper, '确认驳回')!.trigger('click')
    await flushPromises()

    expect(rejectRequest).toHaveBeenCalledWith('r1', { comment: '材料不完整', version: 1 })
    expect(wrapper.emitted('done')).toBeTruthy()
  })

  it('handles 409 conflict and emits done', async () => {
    vi.mocked(approveRequest).mockRejectedValue(
      new ApiError(409, 'APPROVAL_CONFLICT', '申请已发生变化'),
    )
    const wrapper = mountActions(request({ currentStep: 'First' }), approver1)
    await findButton(wrapper, '审批通过')!.trigger('click')
    await flushPromises()
    await findButton(wrapper, '确认通过')!.trigger('click')
    await flushPromises()

    expect(ElMessage.error).toHaveBeenCalled()
    expect(wrapper.emitted('done')).toBeTruthy()
  })

  it('handles 403 and emits done', async () => {
    vi.mocked(rejectRequest).mockRejectedValue(
      new ApiError(403, 'APPROVAL_NOT_ASSIGNED', '只有当前节点的审批人可以操作'),
    )
    const wrapper = mountActions(request({ currentStep: 'First' }), approver1)
    await findButton(wrapper, '驳回')!.trigger('click')
    await flushPromises()
    const textarea = wrapper.find('textarea')
    await textarea.setValue('不同意')
    await findButton(wrapper, '确认驳回')!.trigger('click')
    await flushPromises()

    expect(ElMessage.error).toHaveBeenCalled()
    expect(wrapper.emitted('done')).toBeTruthy()
  })
})

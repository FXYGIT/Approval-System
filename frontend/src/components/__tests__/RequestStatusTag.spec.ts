import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { describe, expect, it } from 'vitest'

import RequestStatusTag from '@/components/RequestStatusTag.vue'
import type { ApprovalStep, RequestStatus } from '@/types/request'

function mountTag(status: RequestStatus, currentStep: ApprovalStep | null = null) {
  return mount(RequestStatusTag, {
    props: { status, currentStep },
    global: { plugins: [ElementPlus] },
  })
}

describe('RequestStatusTag', () => {
  it('renders draft label as info', () => {
    const wrapper = mountTag('Draft')
    expect(wrapper.text()).toBe('草稿')
    expect(wrapper.find('.el-tag').classes()).toContain('el-tag--info')
  })

  it('renders first-step in-progress label', () => {
    expect(mountTag('InProgress', 'First').text()).toBe('一级审批中')
  })

  it('renders second-step in-progress label', () => {
    expect(mountTag('InProgress', 'Second').text()).toBe('二级审批中')
  })

  it('renders approved and rejected labels', () => {
    expect(mountTag('Approved').text()).toBe('已通过')
    expect(mountTag('Rejected').text()).toBe('已驳回')
  })
})

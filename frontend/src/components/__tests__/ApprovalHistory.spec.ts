import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { describe, expect, it } from 'vitest'

import ApprovalHistory from '@/components/ApprovalHistory.vue'
import type { HistoryEntry } from '@/types/history'

function entry(partial: Partial<HistoryEntry>): HistoryEntry {
  return {
    id: 'h1',
    action: 'Submit',
    operator: { id: 'u1', username: 'alice', displayName: 'Alice' },
    step: null,
    comment: null,
    previousStatus: null,
    previousStep: null,
    newStatus: 'InProgress',
    newStep: 'First',
    createdAt: '2026-01-01T00:00:00Z',
    ...partial,
  }
}

function mountHistory(entries: HistoryEntry[]) {
  return mount(ApprovalHistory, {
    props: { entries },
    global: { plugins: [ElementPlus] },
  })
}

describe('ApprovalHistory', () => {
  it('shows empty state when no entries', () => {
    const wrapper = mountHistory([])
    expect(wrapper.text()).toContain('暂无审批记录')
  })

  it('renders action label, operator and comment', () => {
    const wrapper = mountHistory([
      entry({
        id: 'h2',
        action: 'FirstReject',
        operator: { id: 'u2', username: 'bob', displayName: 'Bob' },
        comment: '材料不完整',
      }),
    ])
    expect(wrapper.text()).toContain('一级审批驳回')
    expect(wrapper.text()).toContain('Bob')
    expect(wrapper.text()).toContain('材料不完整')
  })

  it('omits comment when empty', () => {
    const wrapper = mountHistory([entry({ action: 'SecondApprove', comment: null })])
    expect(wrapper.text()).not.toContain('审批意见')
  })

  it('sorts entries by createdAt ascending', () => {
    const wrapper = mountHistory([
      entry({ id: 'b', action: 'SecondApprove', createdAt: '2026-01-03T00:00:00Z' }),
      entry({ id: 'a', action: 'Submit', createdAt: '2026-01-01T00:00:00Z' }),
    ])
    const actions = wrapper.findAll('.action').map((node) => node.text())
    expect(actions).toEqual(['提交申请', '二级审批通过'])
  })
})

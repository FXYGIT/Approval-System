import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      redirect: '/requests',
      children: [
        {
          path: 'requests',
          name: 'requests',
          component: () => import('@/views/RequestListView.vue'),
        },
        {
          path: 'requests/new',
          name: 'request-new',
          component: () => import('@/views/RequestFormView.vue'),
        },
        {
          path: 'requests/:id',
          name: 'request-detail',
          component: () => import('@/views/RequestDetailView.vue'),
        },
        {
          path: 'requests/:id/edit',
          name: 'request-edit',
          component: () => import('@/views/RequestFormView.vue'),
        },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/requests' },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public) {
    if (!auth.isAuthenticated) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (!auth.user) {
      try {
        await auth.loadMe()
      } catch {
        auth.logout()
        return { name: 'login', query: { redirect: to.fullPath } }
      }
    }
  } else if (auth.isAuthenticated) {
    return { name: 'requests' }
  }
  return true
})

export default router

import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import NotesView from '../views/NotesView.vue';
import LedgersView from '../views/LedgersView.vue';
import TodosView from '../views/TodosView.vue';
import LedgerStatisticsView from '../views/LedgerStatisticsView.vue';
import NoteEditor from '../views/NoteEditor.vue';
import NoteView from '../views/NoteView.vue';
import LedgerView from '../views/LedgerView.vue';
import Auth from '../components/Auth.vue';
import { useUserStore } from '../stores/user';
import { useUiStore } from '../stores/ui';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (to.name === 'home') {
      return { left: 0, top: 0 };
    }
    if (savedPosition) {
      return savedPosition;
    }
    return { left: 0, top: 0 };
  },
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Auth,
    },
    {
      path: '/register',
      name: 'register',
      component: Auth,
    },
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/notes',
      name: 'notes',
      component: NotesView
    },
    {
      path: '/ledgers',
      name: 'ledgers',
      component: LedgersView
    },
    {
      path: '/todos',
      name: 'todos',
      component: TodosView
    },
    {
      path: '/statistics',
      name: 'statistics',
      component: LedgerStatisticsView
    },
    {
      path: '/editor/:noteId?',
      name: 'editor',
      component: NoteEditor,
      props: (route) => ({
        noteId: route.params.noteId ? Number(route.params.noteId) : null,
      })
    },
    {
      path: '/note/:noteId',
      name: 'note-view',
      component: NoteView,
      props: true
    },
    {
      path: '/ledger/:ledgerId',
      name: 'ledger-view',
      component: LedgerView,
      props: true
    }
  ]
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  const ui = useUiStore();
  ui.startRouteLoading();
  const isAuthRoute = to.name === 'login' || to.name === 'register';

  if (!userStore.token && !isAuthRoute) {
    next({
      name: 'login',
      query: { redirect: to.fullPath },
    });
    return;
  }

  if (userStore.token && isAuthRoute) {
    next({ name: 'home' });
    return;
  }

  next();
});

router.afterEach(() => {
  const ui = useUiStore();
  ui.stopRouteLoading();
});

router.onError(() => {
  const ui = useUiStore();
  ui.resetRouteLoading();
});

export default router;

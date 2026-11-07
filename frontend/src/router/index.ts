import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import NotesView from '../views/NotesView.vue';
import LedgersView from '../views/LedgersView.vue';
import TodosView from '../views/TodosView.vue';
import LedgerStatisticsView from '../views/LedgerStatisticsView.vue';
import NoteEditor from '../views/NoteEditor.vue';
import NoteView from '../views/NoteView.vue';
import NoteExportView from '../views/NoteExportView.vue';
import LedgerView from '../views/LedgerView.vue';
import SettingsPage from '../views/SettingsPage.vue';
import NotFound from '../views/NotFound.vue';
import ServerError from '../views/ServerError.vue';
import Auth from '../components/Auth.vue';
import { useUserStore } from '../stores/user';
import { useUiStore } from '../stores/ui';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (to.name === 'home') {
      return { left: 0, top: 0 };
    }
    if (to.hash) {
      return { el: to.hash, top: 100 };
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
      path: '/notes/export',
      name: 'note-export',
      component: NoteExportView
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
      path: '/view-share-note',
      name: 'share-note',
      component: NoteView
    },
    {
      path: '/ledger/:ledgerId',
      name: 'ledger-view',
      component: LedgerView,
      props: true
    },
    {
      // 安卓底栏的「设置」：整屏页面，桌面端仍用弹层
      path: '/settings',
      name: 'settings',
      component: SettingsPage
    },
    {
      path: '/500',
      name: 'server-error',
      component: ServerError,
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFound,
    }
  ]
});

router.beforeEach((to, from, next) => {
  const userStore = useUserStore();
  const ui = useUiStore();
  const isAuthRoute = to.name === 'login' || to.name === 'register';
  const isShareRoute = to.name === 'share-note';
  const tokenInStorage = localStorage.getItem("token") || "";

  if (userStore.token !== tokenInStorage) {
    userStore.token = tokenInStorage;
    if (!tokenInStorage) {
      userStore.profile = null;
    }
  }

  if (!userStore.token && !isAuthRoute && !isShareRoute) {
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

  ui.startRouteTransition();
  next();
});

router.afterEach(() => {
  const ui = useUiStore();
  ui.finishRouteTransition();
});

router.onError(() => {
  const ui = useUiStore();
  ui.resetRouteTransition();
});

export default router;

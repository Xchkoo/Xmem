import { createRouter, createWebHistory } from 'vue-router';
import HomeView from '../views/HomeView.vue';
import NotesView from '../components/NotesView.vue';
import LedgersView from '../components/LedgersView.vue';
import TodosView from '../components/TodosView.vue';
import LedgerStatisticsView from '../components/LedgerStatisticsView.vue';
import NoteEditor from '../components/NoteEditor.vue';
import NoteView from '../components/NoteView.vue';
import LedgerView from '../components/LedgerView.vue';
import { useUserStore } from '../stores/user';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
      props: true
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
  if (!userStore.token && to.path !== '/') {
    next('/');
  } else {
    next();
  }
});

export default router;

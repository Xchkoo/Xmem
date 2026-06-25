package com.xmem.android

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.xmem.android.ui.auth.AuthScreen
import com.xmem.android.ui.main.MainContainer
import com.xmem.android.ui.ledgers.LedgerStatisticsScreen
import com.xmem.android.ui.notes.NoteDetailScreen
import com.xmem.android.ui.notes.NoteEditorScreen
import com.xmem.android.ui.navigation.Screen
import com.xmem.android.ui.theme.XmemTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            XmemTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    XmemNavHost()
                }
            }
        }
    }
}

@Composable
fun XmemNavHost() {
    val navController = rememberNavController()
    // TODO: 获取登录状态，决定起始页
    val startDestination = Screen.Login.route

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Login.route) {
            AuthScreen(
                isRegister = false,
                onAuthSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                onToggleMode = {
                    navController.navigate(Screen.Register.route)
                }
            )
        }
        composable(Screen.Register.route) {
            AuthScreen(
                isRegister = true,
                onAuthSuccess = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo(Screen.Register.route) { inclusive = true }
                    }
                },
                onToggleMode = {
                    navController.popBackStack()
                }
            )
        }
        composable(Screen.Home.route) {
            MainContainer(
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(Screen.Home.route) { inclusive = true }
                    }
                },
                onNoteClick = { noteId ->
                    navController.navigate(Screen.NoteDetail.createRoute(noteId.toInt()))
                },
                onAddNote = {
                    navController.navigate(Screen.NoteEditor.createRoute(null))
                },
                onStatisticsClick = {
                    navController.navigate(Screen.Statistics.route)
                }
            )
        }
        composable(Screen.Statistics.route) {
            LedgerStatisticsScreen(
                onBack = { navController.popBackStack() }
            )
        }
        composable(Screen.NoteDetail.route) { backStackEntry ->
            val noteId = backStackEntry.arguments?.getString("noteId")?.toLongOrNull() ?: 0L
            NoteDetailScreen(
                noteId = noteId,
                onBack = { navController.popBackStack() },
                onEdit = { id -> navController.navigate(Screen.NoteEditor.createRoute(id.toInt())) }
            )
        }
        composable(Screen.NoteEditor.route) { backStackEntry ->
            val noteIdStr = backStackEntry.arguments?.getString("noteId")
            val noteId = if (noteIdStr == "-1" || noteIdStr == null) null else noteIdStr.toLongOrNull()
            NoteEditorScreen(
                noteId = noteId,
                onBack = { navController.popBackStack() }
            )
        }
        // ... 其他路由
    }
}

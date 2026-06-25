package com.xmem.android.ui.ledgers

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.BarChart
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.xmem.android.data.model.LedgerEntry
import com.xmem.android.ui.common.UiState
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LedgersScreen(
    onStatisticsClick: () -> Unit,
    onLedgerClick: (Long) -> Unit,
    viewModel: LedgersViewModel = hiltViewModel()
) {
    var quickInput by remember { mutableStateOf("") }
    val state by viewModel.state.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("记账", fontWeight = FontWeight.Bold) },
                actions = {
                    IconButton(onClick = onStatisticsClick) {
                        Icon(Icons.Default.BarChart, contentDescription = "统计")
                    }
                }
            )
        }
    ) { innerPadding ->
        Column(modifier = Modifier.padding(innerPadding)) {
            // Quick Input
            OutlinedTextField(
                value = quickInput,
                onValueChange = { quickInput = it },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                placeholder = { Text("输入记账内容，如：午饭 25") },
                trailingIcon = {
                    IconButton(onClick = {
                        if (quickInput.isNotBlank()) {
                            viewModel.addLedger(quickInput)
                            quickInput = ""
                        }
                    }) {
                        Icon(Icons.Default.Send, contentDescription = "发送")
                    }
                },
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                keyboardActions = KeyboardActions(onSend = {
                    if (quickInput.isNotBlank()) {
                        viewModel.addLedger(quickInput)
                        quickInput = ""
                    }
                }),
                shape = MaterialTheme.shapes.medium
            )

            when (state) {
                is UiState.Loading -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
                is UiState.Success -> {
                    val ledgers = (state as UiState.Success<List<LedgerEntry>>).data
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(bottom = 16.dp)
                    ) {
                        items(ledgers) { ledger ->
                            LedgerItem(
                                ledger = ledger,
                                onClick = { onLedgerClick(ledger.id) }
                            )
                        }
                    }
                }
                is UiState.Error -> {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Text((state as UiState.Error).message, color = MaterialTheme.colorScheme.error)
                    }
                }
                else -> {}
            }
        }
    }
}

@Composable
fun LedgerItem(
    ledger: LedgerEntry,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = {
            Text(
                text = ledger.category ?: "未分类",
                fontWeight = FontWeight.Bold
            )
        },
        supportingContent = {
            Text(ledger.raw_text)
        },
        trailingContent = {
            Text(
                text = "${ledger.amount ?: 0.0} ${ledger.currency}",
                style = MaterialTheme.typography.titleMedium,
                color = if ((ledger.amount ?: 0.0) < 0) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
            )
        },
        modifier = Modifier.clickable(onClick = onClick)
    )
    HorizontalDivider(modifier = Modifier.padding(horizontal = 16.dp), thickness = 0.5.dp, color = MaterialTheme.colorScheme.outlineVariant)
}

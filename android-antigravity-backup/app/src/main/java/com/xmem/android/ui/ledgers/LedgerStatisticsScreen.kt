package com.xmem.android.ui.ledgers

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.patrykandpatrick.vico.compose.m3.common.rememberM3CartesianStyle
import com.patrykandpatrick.vico.compose.cartesian.CartesianChartHost
import com.patrykandpatrick.vico.compose.cartesian.layer.rememberColumnCartesianLayer
import com.patrykandpatrick.vico.compose.cartesian.rememberCartesianChart
import com.patrykandpatrick.vico.compose.cartesian.axis.rememberBottomAxis
import com.patrykandpatrick.vico.compose.cartesian.axis.rememberStartAxis
import com.patrykandpatrick.vico.core.cartesian.data.CartesianChartModelProducer
import com.patrykandpatrick.vico.core.cartesian.data.columnSeries
import com.xmem.android.data.model.LedgerStatistics
import com.xmem.android.ui.common.UiState
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LedgerStatisticsScreen(
    onBack: () -> Unit,
    viewModel: LedgerStatisticsViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsState()
    val modelProducer = remember { CartesianChartModelProducer.build() }

    LaunchedEffect(Unit) {
        viewModel.fetchStatistics()
    }

    LaunchedEffect(state) {
        if (state is UiState.Success) {
            val stats = (state as UiState.Success<LedgerStatistics>).data
            modelProducer.tryRunTransaction {
                columnSeries {
                    series(stats.daily_data.map { it.amount })
                }
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("账本统计", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        }
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            when (state) {
                is UiState.Loading -> {
                    Box(modifier = Modifier.fillMaxWidth().height(200.dp), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                }
                is UiState.Success -> {
                    val stats = (state as UiState.Success<LedgerStatistics>).data
                    
                    Text("本月支出趋势", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    CartesianChartHost(
                        chart = rememberCartesianChart(
                            rememberColumnCartesianLayer(),
                            startAxis = rememberStartAxis(),
                            bottomAxis = rememberBottomAxis(),
                        ),
                        modelProducer = modelProducer,
                        modifier = Modifier.fillMaxWidth().height(250.dp)
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    Text("分类占比", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    stats.category_stats.forEach { category ->
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(category.category)
                            Text("${category.amount} (${String.format("%.1f", category.percentage)}%)")
                        }
                        LinearProgressIndicator(
                            progress = { category.percentage.toFloat() / 100f },
                            modifier = Modifier.fillMaxWidth(),
                            color = MaterialTheme.colorScheme.primary,
                            trackColor = MaterialTheme.colorScheme.surfaceVariant
                        )
                    }
                }
                is UiState.Error -> {
                    Text((state as UiState.Error).message, color = MaterialTheme.colorScheme.error)
                }
                else -> {}
            }
        }
    }
}

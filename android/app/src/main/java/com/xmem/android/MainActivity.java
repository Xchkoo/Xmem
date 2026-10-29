package com.xmem.android;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // 必须在 super.onCreate 之前注册，Bridge 初始化时才会加载插件
        registerPlugin(XmemCapturePlugin.class);
        super.onCreate(savedInstanceState);
    }
}

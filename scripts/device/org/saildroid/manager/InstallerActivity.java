package org.saildroid.manager;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Handler;
import android.graphics.Color;
import android.view.View;
import android.widget.*;
import org.json.JSONObject;
import java.io.File;
import java.util.*;

/** The actual installer/catalog UI; all APK operations use the installation registry. */
public final class InstallerActivity extends Activity {
    private LinearLayout body;
    private TextView status;
    private final Handler main=new Handler();
    private boolean busy;
    private AlertDialog incomingDialog;
    private int dp(int n){return Math.round(n*getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size){TextView view=new TextView(this);view.setText(value);view.setTextSize(size);view.setTextColor(0xff152c3b);view.setPadding(0,dp(8),0,dp(8));return view;}
    private Button button(String title,View.OnClickListener action){Button button=new Button(this);button.setText(title);button.setEnabled(!busy);button.setOnClickListener(action);return button;}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);setTitle("SailDroid");showCatalog();
        try{SdAppRegistry.refreshLaunchers();}catch(Exception error){failure(error);}
        String incoming=System.getProperty("saidroid.install.source");if(incoming!=null&&!incoming.isEmpty()){
            File file=new File(incoming.startsWith("file:")?android.net.Uri.parse(incoming).getPath():incoming);confirm(file);
        }
    }
    @Override protected void onNewIntent(android.content.Intent intent){
        super.onNewIntent(intent);setIntent(intent);
        if(!android.content.Intent.ACTION_VIEW.equals(intent.getAction())||intent.getData()==null)return;
        try{
            android.net.Uri uri=intent.getData();
            if(!"file".equals(uri.getScheme())||uri.getAuthority()!=null&&!uri.getAuthority().isEmpty())throw new java.io.IOException("请选择本地 APK 文件。");
            File file=new File(uri.getPath());if(!file.isFile()||!file.canRead())throw new java.io.IOException("APK 文件无法读取。");
            if(busy){Toast.makeText(this,"请等待当前安装完成后再打开安装包。",Toast.LENGTH_LONG).show();return;}
            confirm(file);
        }catch(Exception error){failure(error);}
    }
    private void page(String title){
        LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(dp(16),dp(20),dp(16),dp(12));root.setBackgroundColor(0xfff4f7fa);
        root.addView(text(title,26));status=text("",15);root.addView(status);
        ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);
    }
    private void showCatalog(){
        page("SailDroid");
        body.addView(button("安装 Android 应用",new View.OnClickListener(){@Override public void onClick(View v){if(!busy)browse(new File(System.getenv("HOME"),"Downloads"));}}));
        body.addView(text("已安装应用",20));
        List<JSONObject> apps=SdAppRegistry.installed();
        System.err.println("INSTALLER=catalog|apps="+apps.size());
        if(apps.isEmpty())body.addView(text("选择 APK 文件即可安装应用。",16));
        for(final JSONObject app:apps){
            LinearLayout row=new LinearLayout(this);row.setOrientation(LinearLayout.VERTICAL);row.setPadding(0,dp(12),0,dp(12));
            LinearLayout heading=new LinearLayout(this);ImageView icon=new ImageView(this);icon.setImageURI(android.net.Uri.fromFile(new File(app.optString("icon"))));heading.addView(icon,new LinearLayout.LayoutParams(dp(56),dp(56)));
            TextView title=text(app.optString("label")+"\n"+app.optString("versionName"),18);heading.addView(title,new LinearLayout.LayoutParams(0,-2,1));row.addView(heading);
            LinearLayout actions=new LinearLayout(this);
            actions.addView(button("打开",new View.OnClickListener(){@Override public void onClick(View v){try{SdAppRegistry.launch(app.getString("package"));status.setText("正在启动 "+app.optString("label")+"…");}catch(Exception error){failure(error);}}}),new LinearLayout.LayoutParams(0,-2,1));
            actions.addView(button("卸载",new View.OnClickListener(){@Override public void onClick(View v){new AlertDialog.Builder(InstallerActivity.this).setTitle("卸载 "+app.optString("label")+"？").setMessage("应用和它在 SailDroid 内的数据将被移除。").setNegativeButton("取消",null).setPositiveButton("卸载",new android.content.DialogInterface.OnClickListener(){@Override public void onClick(android.content.DialogInterface dialog,int which){uninstall(app.optString("package"));}}).show();}}),new LinearLayout.LayoutParams(0,-2,1));
            row.addView(actions);body.addView(row);
        }
    }
    private void browse(final File directory){
        page("选择 APK");status.setText(directory.getAbsolutePath());
        System.err.println("INSTALLER=browser|directory="+directory.getAbsolutePath());
        body.addView(button("返回应用列表",new View.OnClickListener(){@Override public void onClick(View v){showCatalog();}}));
        if(directory.getParentFile()!=null)body.addView(button("上一级",new View.OnClickListener(){@Override public void onClick(View v){browse(directory.getParentFile());}}));
        File[] entries=directory.listFiles();if(entries==null){body.addView(text("此目录无法读取。",16));return;}
        Arrays.sort(entries,new Comparator<File>(){@Override public int compare(File a,File b){if(a.isDirectory()!=b.isDirectory())return a.isDirectory()?-1:1;return a.getName().compareToIgnoreCase(b.getName());}});
        for(final File file:entries){if(!file.isDirectory()&&!file.getName().toLowerCase(Locale.US).endsWith(".apk"))continue;
            body.addView(button((file.isDirectory()?"文件夹 · ":"")+file.getName(),new View.OnClickListener(){@Override public void onClick(View v){if(file.isDirectory())browse(file);else confirm(file);}}));
        }
    }
    private void confirm(final File file){
        if(busy)return;
        if(incomingDialog!=null)incomingDialog.dismiss();
        System.err.println("INSTALLER=confirm|file="+file.getName());
        incomingDialog=new AlertDialog.Builder(this).setTitle("安装 Android 应用").setMessage(file.getName()).setNegativeButton("取消",null).setPositiveButton("安装",new android.content.DialogInterface.OnClickListener(){@Override public void onClick(android.content.DialogInterface dialog,int which){install(file);}}).show();
    }
    private void install(final File file){
        busy=true;showCatalog();status.setText("正在读取安装包…");
        new Thread(new Runnable(){@Override public void run(){try{
            final JSONObject installed=SdAppRegistry.install(file,new SdAppRegistry.Progress(){@Override public void update(final String message){main.post(new Runnable(){@Override public void run(){status.setText(message);}});}});
            main.post(new Runnable(){@Override public void run(){busy=false;showCatalog();status.setText(installed.optString("label")+" 安装完成");System.err.println("INSTALLER=installed|package="+installed.optString("package"));}});
        }catch(final Exception|LinkageError error){main.post(new Runnable(){@Override public void run(){busy=false;showCatalog();failure(error);}});}}},"SailDroid installer").start();
    }
    private void uninstall(final String name){
        if(busy)return;busy=true;showCatalog();status.setText("正在卸载应用…");
        new Thread(new Runnable(){public void run(){try{
            SdAppRegistry.uninstall(name);
            main.post(new Runnable(){public void run(){busy=false;showCatalog();status.setText("卸载完成");System.err.println("INSTALLER=uninstalled|package="+name);}});
        }catch(final Exception|LinkageError error){main.post(new Runnable(){public void run(){busy=false;showCatalog();failure(error);}});}}},"SailDroid uninstaller").start();
    }
    private void failure(Throwable error){error.printStackTrace();String message=error instanceof LinkageError?"此应用使用了尚不支持的 Android 功能。":error.getMessage();new AlertDialog.Builder(this).setTitle("操作未完成").setMessage(message==null?"请确认安装包可读取，且与当前设备兼容。":message).setPositiveButton("确定",null).show();}
}

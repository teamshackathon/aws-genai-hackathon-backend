@echo off
setlocal enabledelayedexpansion
chcp 65001

:: 引数を受け取る
set "service=%1"
set "message=%2"

:: メッセージから数字を抽出 (AAGC2-数字_何か の形式)
set "number="
for /f "tokens=1 delims=_" %%i in ("!message!") do (
    for /f "tokens=2 delims=-" %%j in ("%%i") do (
        set "number=%%j"
    )
)

:: 数字が取得できたか確認
if not defined number (
    echo [警告] メッセージから数字を抽出できませんでした: !message!
) else (
    echo !number!
)

:: .envファイルの存在確認
if not exist ".env" (
    echo [エラー] .envファイルが見つかりません。
    echo 以下のGoogle Driveよりenvをダウンロードしてください： https://drive.google.com/xxxxx
    exit /b 1
)

:: .envファイルから環境変数を取得
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    set "%%A=%%B"
)

if "%service%" equ "discord" (

    :: 取得先のJSONファイル名
    set "JSON_FILE=response.json"
    
    set "url=https://api.notion.com/v1/databases/!NOTION_DATABASE_ID!/query"
    
    :: Notion APIからデータを取得し、JSONファイルに保存
    curl -X POST ^
      -H "Authorization: Bearer !NOTION_API_KEY!" ^
      -H "Notion-Version: 2022-06-28" ^
      -H "Content-Type: application/json" ^
      -d "{\"filter\": {\"property\": \"ID\",\"number\": {\"equals\": !number!}}}" ^
      !url! > !JSON_FILE!
      
    :: JSONファイル内のプロパティ名を置換 (UTF-8で読み込み、デフォルトエンコーディングで保存)
    powershell -Command "$content = Get-Content -Path !JSON_FILE! -Encoding UTF8; $content = $content -replace 'タスク名', 'task_name' -replace '担当者', 'assignee'; $content | Out-File -FilePath '!JSON_FILE!' -Encoding UTF8"
    
    
    for /f "usebackq delims=" %%i in (`tools\jq -r ".results[0].properties.task_name.title[0].plain_text" "!JSON_FILE!"`) do (
        set "task_name=%%i"
    )

    for /f "usebackq delims=" %%i in (`tools\jq -r ".results[0].properties.assignee.people[0].name" "!JSON_FILE!"`) do (
        set "assignee=%%i"
    )

    for /f "usebackq delims=" %%i in (`tools\jq -r ".results[0].properties.assignee.people[0].avatar_url" "!JSON_FILE!"`) do (
        set "avatar_url=%%i"
    )

    for /f "usebackq delims=" %%i in (`tools\jq -r ".results[0].url" "!JSON_FILE!"`) do (
        set "url=%%i"
    )

    :: 現在のISO形式のタイムスタンプを取得
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "$now = Get-Date; $now.ToString('yyyy/MM/dd HH:mm')"` ) do (
        set "timestamp=%%i"
    )

    :: ランダムな色を生成する（10進数で0〜16777215の範囲）
    for /f "usebackq delims=" %%i in (`powershell -NoProfile -Command "$rnd = Get-Random -Minimum 0 -Maximum 16777215; $rnd"`) do (
        set "color=%%i"
    )

    :: メッセージを送信
    curl -H "Content-Type: application/json" -X POST -d "{\"embeds\":[{\"title\": \"【!message!】!task_name!\",\"color\":\"!color!\",\"url\":\"!url!\",\"author\": {\"name\": \"!assignee!\",\"icon_url\": \"!avatar_url!\"},\"footer\": {\"text\": \"!timestamp!\"}}]}" !DISCORD_WEBHOOK!

    :: 一時ファイルを削除
    if exist "!JSON_FILE!" del /f /q "!JSON_FILE!"
    echo [情報] 一時ファイルを削除しました: !JSON_FILE!
)

endlocal
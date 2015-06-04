param(
    [Parameter(Mandatory=$true,Position=0)][string] $file
)

Set-ItemProperty -Path $file -Name LastWriteTime -Value (Get-Date)
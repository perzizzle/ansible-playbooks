#!powershell
# Michael Perzel 1/22/2014
# WANT_JSON
# POWERSHELL_COMMON

$params = Parse-Args $args;

$result = New-Object PSObject -Property @{
    changed = $false
    success = $false
    output = ""
}

If ($params.source) {
    $source = $params.source
}
Else {
    Fail-Json (New-Object PSObject $fail) "missing required argument: source"
}

If ($params.destination) {
    $destination = $params.destination
}
Else {
    Fail-Json (New-Object PSObject $fail) "missing required argument: destination"
}

If ($params.include) {
    $include = $params.include
}
If ($params.exclude) {
    $exclude = $params.exclude
}

If ($params.creates) {
    $creates = $params.creates
}

If( $creates -and (Test-Path $destination/$creates)) {
    $result.output += "File already exists, not unzipping"
    $result.success = $true
    Exit-Json $result
}

If(!(Test-Path $source)) {
    Fail-Json (New-Object PSObject $fail) "$source file does not exist"
}

try {
    $psource = $source
    if($include){
        $psource = '{0}\{1}' -f $psource, $include
    }

    $result.output += "Extract-ZipFile"
    $result.output += ("Extracting Zip File from {0} to {1}" -f $psource, $destination)
    $shell_app = new-object -com shell.application
    $sourceFolder = $shell_app.namespace($source)
    $destFolder = $shell_app.namespace($destination)
    $items = $sourceFolder.Items()
    if($include){
        $items = $sourceFolder.Items() | ?{$_.Name -eq $include}
    }
    elseif($exclude){
        $items = $sourceFolder.Items() | ?{$_.Name -ne $exclude}
    }

    $items | ?{ $_.IsFolder } | %{ $destFolder.CopyHere($_.GetFolder, 16) }
    $items | ?{ !$_.IsFolder } | %{ $destFolder.CopyHere($_, 16) }

    $result.output += ('Extracting {0} complete.' -f $psource)

    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($shell_app) | Out-Null
    $result.success = $true
    $result.changed = $true

}
catch {
    Fail-Json (New-Object PSObject $fail)  $_.Exception.Message
}

If ($result.success) {
    Exit-Json $result
}

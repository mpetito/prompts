<#
.SYNOPSIS
    Shared Word COM plumbing for the docx editing toolkit.

.DESCRIPTION
    Every script in this folder drives Microsoft Word itself rather than editing the
    underlying OOXML. Word does the writing, so formatting fidelity is guaranteed by
    construction and tracked changes are genuine Word revisions.

    Import with:  Import-Module "$PSScriptRoot\WordCom.psm1" -Force
#>

Set-StrictMode -Version Latest

# Word enum values we use (avoids needing the interop assembly).
$script:WdConst = @{
    wdFormatPDF                 = 17
    wdFormatXMLDocument         = 12
    wdExportFormatPDF           = 17
    wdExportOptimizeForPrint    = 0
    wdExportAllDocument         = 0
    wdExportDocumentContent     = 0
    wdExportCreateHeadingBookmarks = 1
    wdRevisionInsert            = 1
    wdRevisionDelete            = 2
    wdRevisionProperty          = 3
    wdReplaceOne                = 1
    wdReplaceAll                = 2
    wdFindStop                  = 0
    wdFindContinue              = 1
    wdActiveEndPageNumber       = 3
    wdFirstCharacterLineNumber  = 10
    wdStory                     = 6
    wdGoToPage                  = 1
    wdDoNotSaveChanges          = 0
    wdAlertsNone                = 0
}
function Get-WdConst { param([Parameter(Mandatory)][string]$Name) $script:WdConst[$Name] }
Export-ModuleMember -Function Get-WdConst

<#
.SYNOPSIS Start an invisible Word instance configured for unattended automation.
#>
function New-WordApp {
    [CmdletBinding()]
    param(
        # Leave revision marks on for the session. Individual scripts set this per-document.
        [switch]$Visible
    )
    $word = New-Object -ComObject Word.Application
    $word.Visible = [bool]$Visible
    $word.DisplayAlerts = $script:WdConst.wdAlertsNone
    # Suppress the "document contains macros / links" style prompts that would block us.
    try { $word.AutomationSecurity = 3 } catch { }   # msoAutomationSecurityForceDisable
    try { $word.Options.SaveNormalPrompt = $false } catch { }
    try { $word.Options.WarnBeforeSavingPrintingSendingMarkup = $false } catch { }
    $word
}
Export-ModuleMember -Function New-WordApp

<#
.SYNOPSIS Close a Word instance and release its COM handles.
.DESCRIPTION
    Word is notorious for surviving a failed script as an orphan WINWORD.exe holding a
    file lock. Always call this from a finally{} block.
#>
function Remove-WordApp {
    [CmdletBinding()]
    param([Parameter(Mandatory)]$Word)
    if ($null -eq $Word) { return }
    try { $Word.Quit($script:WdConst.wdDoNotSaveChanges) } catch { }
    try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($Word) } catch { }
    [GC]::Collect(); [GC]::WaitForPendingFinalizers()
}
Export-ModuleMember -Function Remove-WordApp

<#
.SYNOPSIS Open a document, resolving the path and defaulting to read-only.
#>
function Open-WordDocument {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]$Word,
        [Parameter(Mandatory)][string]$Path,
        [switch]$Writable
    )
    $full = (Resolve-Path -LiteralPath $Path).ProviderPath
    # Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles, ..., Visible)
    $doc = $Word.Documents.Open($full, $false, (-not $Writable), $false)
    $doc
}
Export-ModuleMember -Function Open-WordDocument

<#
.SYNOPSIS Kill orphaned WINWORD processes left over from a crashed automation run.
.DESCRIPTION
    Only touches processes with no visible main window, so a Word instance the user has
    open by hand is left alone.
#>
function Stop-OrphanWord {
    [CmdletBinding(SupportsShouldProcess)]
    param()
    Get-Process WINWORD -ErrorAction SilentlyContinue |
        Where-Object { $_.MainWindowTitle -eq '' } |
        ForEach-Object {
            if ($PSCmdlet.ShouldProcess("WINWORD pid $($_.Id)", 'Stop-Process')) {
                Stop-Process -Id $_.Id -Force
            }
        }
}
Export-ModuleMember -Function Stop-OrphanWord

<#
.SYNOPSIS Make a timestamp-suffixed working copy so the original is never touched.
#>
function New-WorkingCopy {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [string]$Suffix = 'work',
        [string]$Destination
    )
    $src = Get-Item -LiteralPath $Path
    if (-not $Destination) {
        $Destination = Join-Path $src.DirectoryName "$($src.BaseName).$Suffix$($src.Extension)"
    }
    $dir = Split-Path -Parent $Destination
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Copy-Item -LiteralPath $src.FullName -Destination $Destination -Force
    (Resolve-Path -LiteralPath $Destination).ProviderPath
}
Export-ModuleMember -Function New-WorkingCopy

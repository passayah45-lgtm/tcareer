param(
    [Parameter(Mandatory = $true)]
    [string]$BaseUrl,

    [string]$ApiUrl = "$BaseUrl/api/v1",
    [string]$ComposeFile = "docker-compose.staging.yml",
    [string]$EnvFile = ".env.staging",
    [string]$LoadProfile = "smoke",
    [string]$Token = "",
    [string]$OrganizationId = "",
    [switch]$SkipLoadTest
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )
    Write-Host "==> $Name"
    & $Command
}

if (-not (Test-Path $EnvFile)) {
    throw "$EnvFile is missing. Copy env.example.staging to $EnvFile on the staging host and fill secrets outside source control."
}

Invoke-Step "Docker Compose config validation" {
    docker compose --env-file $EnvFile -f $ComposeFile config | Out-Null
}

Invoke-Step "Build staging images" {
    docker compose --env-file $EnvFile -f $ComposeFile build
}

Invoke-Step "Start staging stack" {
    docker compose --env-file $EnvFile -f $ComposeFile up -d
}

Invoke-Step "Release candidate check" {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T web python manage.py release_candidate_check --json
}

Invoke-Step "Production smoke check" {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T web python manage.py production_smoke_check
}

Invoke-Step "Provider configuration check" {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T web python manage.py validate_production_providers --json
}

Invoke-Step "Retention dry run" {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T web python manage.py run_retention_policies --dry-run --json
}

Invoke-Step "Backup restore readiness probe" {
    docker compose --env-file $EnvFile -f $ComposeFile exec -T web python manage.py backup_restore_check --dry-run --fail-on-warning
}

if (-not $SkipLoadTest) {
    $args = @("tools/load_tests/tcareer_load.py", "--base-url", $ApiUrl, "--profile", $LoadProfile)
    if ($Token) {
        $args += @("--token", $Token)
    }
    if ($OrganizationId) {
        $args += @("--organization-id", $OrganizationId)
    }
    Invoke-Step "Load test profile: $LoadProfile" {
        python @args
    }
}

Write-Host "Staging rehearsal command sequence completed. Review output before marking any step passed."

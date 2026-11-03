$base = "http://127.0.0.1:8000"
$cases = @(
  @{ name='geology/grid';           url="$base/api/engine/geology/grid";           body=@{ nx=2; ny=2; nz=1; dx=50; dy=50; dz=10 } },
  @{ name='reservoir/nodal';        url="$base/api/engine/reservoir/nodal";        body=@{ qi=1000; pr=3000; p_surf=500; a=0.002; b=10 } },
  @{ name='drilling/trajectory';    url="$base/api/engine/drilling/trajectory";    body=@{ survey=@(@{md=0;inc=0;azi=0}, @{md=500;inc=15;azi=45}); md_col='md'; inc_col='inc'; azi_col='azi' } },
  @{ name='pvt/eos';                url="$base/api/engine/pvt/eos";                body=@{ pressure=2500; temperature=350; components=@(@{name='C1';critical_pressure=667;critical_temperature=343;acentric_factor=0.011;molecular_weight=16}); composition=@{C1=1}; eos_type='PR'; binary_interactions=@() } }
)
foreach ($c in $cases) {
  try {
    $r = Invoke-WebRequest -Uri $c.url -Method POST -Body ($c.body | ConvertTo-Json -Depth 10) -ContentType 'application/json' -TimeoutSec 15 -ErrorAction Stop
    "PASS  $($c.name)  HTTP $($r.StatusCode)"
  } catch {
    "FAIL  $($c.name)  $($_.Exception.Response.StatusCode.value__)  $($_.Exception.Message)"
  }
}
